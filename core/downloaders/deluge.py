import logging
import json
import zlib

from lib.deluge_client import DelugeRPCClient

import core
from core.helpers import Torrent, Url

logging = logging.getLogger(__name__)


class DelugeRPC(object):

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to deluge daemon rpc
        data: dict of deluge server information

        Tests if we can open a socket to the rpc

        Return True on success or str error message on failure
        '''

        host = data['host']
        port = data['port']
        user = data['user']
        password = data['pass']

        client = DelugeRPCClient(host, port, user, password)
        try:
            error = client.connect()
            if error:
                return '{}.'.format(error)
        except Exception as e:
            return str(e)
        return True

    @staticmethod
    def add_torrent(data):
        ''' Adds torrent or magnet to Deluge
        data: dict of torrrent/magnet information

        Returns dict {'response': True, 'download_id': 'id'}
                     {'response': False, 'error': 'exception'}

        '''
        conf = core.CONFIG['Downloader']['Torrent']['DelugeRPC']

        host = conf['host']
        port = conf['port']
        user = conf['user']
        password = conf['pass']

        client = DelugeRPCClient(host, port, user, password)

        try:
            error = client.connect()
            if error:
                return {'response': False, 'error': error}
        except Exception as e:
            logging.error('Deluge Add Torrent.', exc_info=True)
            return {'response': False, 'error': str(e)}

        try:
            def_download_path = client.call('core.get_config')[b'download_location'].decode('utf-8')
        except Exception as e:
            logging.error('Unable to get download path.', exc_info=True)
            return {'response': False, 'error': 'Unable to get download path.'}

        download_path = '{}/{}'.format(def_download_path, conf['category'])

        priority_keys = {
            'Normal': 0,
            'High': 128,
            'Max': 255
        }

        options = {}
        options['add_paused'] = conf['addpaused']
        options['download_location'] = download_path
        options['priority'] = priority_keys[conf['priority']]

        if data['type'] == 'magnet':
            try:
                download_id = client.call('core.add_torrent_magnet', data['torrentfile'], options).decode('utf-8')
                return {'response': True, 'downloadid': download_id}
            except Exception as e:
                logging.error('Unable to send magnet.', exc_info=True)
                return {'response': False, 'error': str(e)}
        elif data['type'] == 'torrent':
            try:
                download_id = client.call('core.add_torrent_url', data['torrentfile'], options).decode('utf-8')
                return {'response': True, 'downloadid': download_id}
            except Exception as e:
                logging.error('Unable to send magnet.', exc_info=True)
                return {'response': False, 'error': str(e)}
        return


class DelugeWeb(object):

    cookie = None
    retry = False
    command_id = 0

    headers = {'Content-Type': 'application/json', 'User-Agent': 'Watcher'}

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to deluge web client
        data: dict of deluge server information


        Return True on success or str error message on failure
        '''

        host = data['host']
        port = data['port']
        password = data['pass']

        url = '{}:{}/json'.format(host, port)

        return DelugeWeb._login(url, password)

    @staticmethod
    def add_torrent(data):
        ''' Adds torrent or magnet to deluge web api
        data: dict of torrrent/magnet information

        Adds torrents to default/path/<category>

        Returns dict {'response': True, 'download_id': 'id'}
                     {'response': False, 'error': 'exception'}

        '''

        conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']

        host = conf['host']
        port = conf['port']
        url = '{}:{}/json'.format(host, port)

        priority_keys = {
            'Normal': 0,
            'High': 128,
            'Max': 255
        }

        if DelugeWeb.cookie is None:
            if DelugeWeb._login(url, conf['pass']) is not True:
                return {'response': False, 'error': 'Incorrect usename or password.'}

        download_dir = DelugeWeb._get_download_dir(url)

        if not download_dir:
            return {'response': False, 'error': 'Unable to get path information.'}
        # if we got download_dir we can connect.

        download_dir = '{}/{}'.format(download_dir, conf['category'])

        # if file is a torrent, have deluge download it to a tmp dir
        if data['type'] == 'torrent':
            tmp_torrent_file = DelugeWeb._get_torrent_file(data['torrentfile'], url)
            if tmp_torrent_file['response'] is True:
                data['torrentfile'] = tmp_torrent_file['torrentfile']
            else:
                return {'response': False, 'error': tmp_torrent_file['error']}

        torrent = {'path': data['torrentfile'], 'options': {}}
        torrent['options']['add_paused'] = conf['addpaused']
        torrent['options']['download_location'] = download_dir
        torrent['options']['priority'] = priority_keys[conf['priority']]

        command = {'method': 'web.add_torrents',
                   'params': [[torrent]],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        post_data = json.dumps(command)
        request = Url.request(url, post_data=post_data, headers=DelugeWeb.headers)
        request.add_header('cookie', DelugeWeb.cookie)

        try:
            response = Url.open(request, read_bytes=True)
            response = DelugeWeb._read(response['body'])
            if response['result'] is True:
                downloadid = Torrent.get_hash(data['torrentfile'])
                return {'response': True, 'downloadid': downloadid}
            else:
                return {'response': False, 'error': response['error']}
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Delugeweb add_torrent', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def _get_torrent_file(torrent_url, deluge_url):
        command = {'method': 'web.download_torrent_from_url',
                   'params': [torrent_url],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1
        post_data = json.dumps(command)
        request = Url.request(deluge_url, post_data=post_data, headers=DelugeWeb.headers)
        request.add_header('cookie', DelugeWeb.cookie)
        try:
            response = Url.open(request, read_bytes=True)
            response = DelugeWeb._read(response['body'])
            if response['error'] is None:
                return {'response': True, 'torrentfile': response['result']}
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Delugeweb download_torrent_from_url', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def _get_download_dir(url):

        command = {'method': 'core.get_config_value',
                   'params': ['download_location'],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        post_data = json.dumps(command)

        request = Url.request(url, post_data=post_data, headers=DelugeWeb.headers)
        request.add_header('cookie', DelugeWeb.cookie)

        try:
            response = Url.open(request, read_bytes=True)
            response = DelugeWeb._read(response['body'])
            return response['result']
        except Exception as e:
            logging.error('delugeweb get_download_dir', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def _read(response):
        ''' Reads gzipped json response into dict
        '''

        return json.loads(zlib.decompress(response, 16+zlib.MAX_WBITS))

    @staticmethod
    def _login(url, password):

        command = {'method': 'auth.login',
                   'params': [password],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        post_data = json.dumps(command)

        request = Url.request(url, post_data, headers=DelugeWeb.headers)

        try:
            response = Url.open(request, read_bytes=True)
            DelugeWeb.cookie = response['headers'].get('Set-Cookie')

            if DelugeWeb.cookie is None:
                return 'Incorrect password.'

            body = DelugeWeb._read(response['body'])
            if body['error'] is None:
                return True
            else:
                return response.msg

        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('DelugeWeb test_connection', exc_info=True)
            return '{}.'.format(e)

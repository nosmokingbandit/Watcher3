import logging
import json
import re

from lib.deluge_client import DelugeRPCClient

import core
from core.helpers import Torrent, Url

logging.getLogger('lib.deluge_client').setLevel(logging.CRITICAL)
logging = logging.getLogger(__name__)

label_fix = re.compile('[^a-z0-9_-]')


class DelugeRPC(object):

    @staticmethod
    def test_connection(config):
        ''' Tests connectivity to deluge daemon rpc
        config: dict of deluge server information

        Tests if we can open a socket to the rpc and creates DelugeRPC.client if successful

        Returns Bool True on success or str error message on failure
        '''

        host = config['host']
        port = config['port']
        user = config['user']
        password = config['pass']

        client = DelugeRPCClient(host, port, user, password)
        try:
            error = client.connect()
            if error:
                return '{}.'.format(error)
        except Exception as e:
            logging.error('Unable to connect to Deluge RPC.', exc_info=True)
            return str(e)
        else:
            return True

    @staticmethod
    def add_torrent(torrent):
        ''' Adds torrent or magnet to Deluge
        torrent: dict of torrrent/magnet information

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

        if torrent['type'] == 'magnet':
            try:
                download_id = client.call('core.add_torrent_magnet', torrent['torrentfile'], options).decode('utf-8')
            except Exception as e:
                logging.error('Unable to send magnet.', exc_info=True)
                return {'response': False, 'error': str(e)}
        elif torrent['type'] == 'torrent':
            try:
                download_id = client.call('core.add_torrent_url', torrent['torrentfile'], options).decode('utf-8')
            except Exception as e:
                logging.error('Unable to send magnet.', exc_info=True)
                return {'response': False, 'error': str(e)}
        else:
            return {'response': False, 'error': 'Invalid torrent type {}'.format(torrent['type'])}

        DelugeRPC._set_label(download_id, conf['category'])

        return {'response': True, 'downloadid': download_id}

    @staticmethod
    def cancel_download(downloadid):
        ''' Cancels download in client
        downloadid: int download id
        Returns bool
        '''
        logging.info('Cancelling download # {}'.format(downloadid))

        conf = core.CONFIG['Downloader']['Torrent']['DelugeRPC']

        host = conf['host']
        port = conf['port']
        user = conf['user']
        password = conf['pass']

        client = DelugeRPCClient(host, port, user, password)

        try:
            client.connect()
            return client.call('core.remove_torrent', downloadid, True)
        except Exception as e:
            logging.error('Unable to cancel download.', exc_info=True)
            return False

    @staticmethod
    def _set_label(torrent, label, client):
        ''' Sets label for download
        torrent: str hash of torrent to apply label
        label: str name of label to apply
        client: object DelugeRPCClient instance

        Returns Bool
        '''

        label = label_fix.sub('', label.lower()).encode('utf-8')

        logging.info('Applying label {} to torrent {}.'.format(label, torrent))

        if b' ' in label:
            logging.error('Deluge label cannot contain spaces.')
            return False

        try:
            deluge_labels = client.call('label.get_labels')
        except Exception as e:
            logging.error('Unable to get labels from DelugeRPC.', exc_info=True)

        if label not in deluge_labels:
            logging.info('Adding label {} to Deluge'.format(label))
            try:
                client.call('label.add', label)
            except Exception as e:
                logging.error('Unable to add Deluge label.', exc_info=True)
                return False

        try:
            l = client.call('label.set_torrent', torrent, label)
            if l == b'Unknown Label':
                logging.error('Unknown label {}'.format(label))
                return False
        except Exception as e:
            logging.error('Unable to set Deluge label.', exc_info=True)
            return False

        return True


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
        headers = DelugeWeb.headers
        headers['cookie'] = DelugeWeb.cookie

        try:
            response = Url.open(url, post_data=post_data, headers=DelugeWeb.headers)
            response = json.loads(response.text)
            if response['result'] is True:
                downloadid = Torrent.get_hash(data['torrentfile'])
            else:
                return {'response': False, 'error': response['error']}
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Delugeweb add_torrent', exc_info=True)
            return {'response': False, 'error': str(e)}

        DelugeWeb._set_label(downloadid, conf['category'], url)

        return {'response': True, 'downloadid': downloadid}

    @staticmethod
    def _set_label(torrent, label, url):
        ''' Sets label for download
        torrent: str hash of torrent to apply label
        label: str name of label to apply
        url: str url of deluge web interface

        Returns bool
        '''
        label = label_fix.sub('', label.lower())

        command = {'method': 'label.get_labels',
                   'params': [],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        try:
            response = Url.open(url, post_data=json.dumps(command), headers=DelugeWeb.headers).text
            deluge_labels = json.loads(response).get('result', [])
        except Exception as e:
            logging.error('Unable to get labels from Deluge Web UI.', exc_info=True)
            return False

        if label not in deluge_labels:
            logging.info('Adding label {} to Deluge.'.format(label))
            command = {'method': 'label.add',
                       'params': [label],
                       'id': DelugeWeb.command_id
                       }
            DelugeWeb.command_id += 1
            try:
                sc = Url.open(url, post_data=json.dumps(command), headers=DelugeWeb.headers).status_code
                if sc != 200:
                    logging.error('Deluge Web UI response {}.'.format(sc))
                    return False
            except Exception as e:
                logging.error('Delugeweb get_labels.', exc_info=True)
                return False
        try:
            command = {'method': 'label.set_torrent',
                       'params': [torrent.lower(), label],
                       'id': DelugeWeb.command_id
                       }
            DelugeWeb.command_id += 1
            sc = Url.open(url, post_data=json.dumps(command), headers=DelugeWeb.headers).status_code
            if sc != 200:
                logging.error('Deluge Web UI response {}.'.format(sc))
                return False
        except Exception as e:
            logging.error('Delugeweb set_torrent.', exc_info=True)
            return False

        return True

    @staticmethod
    def _get_torrent_file(torrent_url, deluge_url):
        command = {'method': 'web.download_torrent_from_url',
                   'params': [torrent_url],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1
        post_data = json.dumps(command)
        headers = DelugeWeb.headers
        headers['cookie'] = DelugeWeb.cookie
        try:
            response = Url.open(deluge_url, post_data=post_data, headers=headers)
            response = json.loads(response.text)
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

        headers = DelugeWeb.headers
        headers['cookie'] = DelugeWeb.cookie

        try:
            response = Url.open(url, post_data=post_data, headers=headers)
            response = json.loads(response.text)
            return response['result']
        except Exception as e:
            logging.error('delugeweb get_download_dir', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def _login(url, password):

        command = {'method': 'auth.login',
                   'params': [password],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        post_data = json.dumps(command)

        try:
            response = Url.open(url, post_data=post_data, headers=DelugeWeb.headers)
            DelugeWeb.cookie = response.headers.get('Set-Cookie')

            if DelugeWeb.cookie is None:
                return 'Incorrect password.'

            body = json.loads(response.text)
            if body['error'] is None:
                return True
            else:
                return response.msg

        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('DelugeWeb test_connection', exc_info=True)
            return '{}.'.format(e)

    @staticmethod
    def cancel_download(downloadid):

        conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']

        host = conf['host']
        port = conf['port']
        url = '{}:{}/json'.format(host, port)

        if DelugeWeb.cookie is None:
            DelugeWeb._login(url, conf['pass'])

        command = {'method': 'core.remove_torrent',
                   'params': [downloadid.lower(), True],
                   'id': DelugeWeb.command_id
                   }
        DelugeWeb.command_id += 1

        post_data = json.dumps(command)

        headers = DelugeWeb.headers
        headers['cookie'] = DelugeWeb.cookie

        try:
            response = Url.open(url, post_data=post_data, headers=headers)
            response = json.loads(response.text)
            return response['result']
        except Exception as e:
            logging.error('delugeweb get_download_dir', exc_info=True)
            return {'response': False, 'error': str(e)}

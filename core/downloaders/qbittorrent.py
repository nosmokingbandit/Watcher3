import logging
import json
import urllib
import urllib.request

import core
from core.helpers import Torrent, Url

logging = logging.getLogger(__name__)


class QBittorrent(object):

    cookie = None
    retry = False

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to qbittorrent
        data: dict of qbittorrent server information

        Return True on success or str error message on failure
        '''

        host = data['host']
        port = data['port']
        user = data['user']
        password = data['pass']

        url = '{}:{}/'.format(host, port)

        return QBittorrent._login(url, user, password)

    @staticmethod
    def add_torrent(data):
        ''' Adds torrent or magnet to qbittorrent
        data: dict of torrrent/magnet information

        Adds torrents to default/path/<category>

        Returns dict {'response': True, 'download_id': 'id'}
                     {'response': False, 'error': 'exception'}

        '''

        conf = core.CONFIG['Downloader']['Torrent']['QBittorrent']

        host = conf['host']
        port = conf['port']
        base_url = '{}:{}/'.format(host, port)

        user = conf['user']
        password = conf['pass']

        if QBittorrent.cookie is None:
            QBittorrent._login(base_url, user, password)

        download_dir = QBittorrent._get_download_dir(base_url)

        if not download_dir:
            return {'response': False, 'error': 'Unable to get path information.'}
        # if we got download_dir we can connect.

        post_data = {}

        post_data['urls'] = data['torrentfile']

        post_data['savepath'] = '{}{}'.format(download_dir, conf['category'])

        post_data['category'] = conf['category']

        url = '{}command/download'.format(base_url)
        post_data = urllib.parse.urlencode(post_data)
        request = Url.request(url, post_data=post_data)
        request.add_header('cookie', QBittorrent.cookie)

        try:
            Url.open(request)  # QBit returns an empty string
            downloadid = Torrent.get_hash(data['torrentfile'])
            return {'response': True, 'downloadid': downloadid}
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('QBittorrent connection test failed.', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def _get_download_dir(base_url):
        try:
            url = '{}query/preferences'.format(base_url)
            request = Url.request(url)
            request.add_header('cookie', QBittorrent.cookie)
            response = json.loads(Url.open(request)['body'])
            return response['save_path']
        except Exception as e:
            logging.error('QBittorrent unable to get download dir.', exc_info=True)
            return {'response': False, 'error': str(e)}

    @staticmethod
    def get_torrents(base_url):
        url = '{}query/torrents'.format(base_url)
        request = Url.request(url)
        request.add_header('cookie', QBittorrent.cookie)
        return Url.open(request)

    @staticmethod
    def _login(url, username, password):

        post_data = urllib.parse.urlencode({'username': username, 'password': password})

        url = '{}login'.format(url)
        request = Url.request(url, post_data=post_data)

        try:
            response = Url.open(request)
            QBittorrent.cookie = response['headers'].get('Set-Cookie')

            if response['body'] == 'Ok.':
                return True
            elif response['body'] == 'Fails.':
                return 'Incorrect usename or password'
            else:
                return response['body']

        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('qbittorrent test_connection', exc_info=True)
            return '{}.'.format(str(e))

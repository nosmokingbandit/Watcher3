import logging
from lib import rtorrent
import core
import xmlrpc.client
from core.helpers import Torrent
from urllib.parse import urlparse

logging = logging.getLogger(__name__)


class rTorrentSCGI(object):

    client = None

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to rtorrent. Also used to create client object.
        data: dict of rtorrent server information

        Return True on success or str error message on failure
        '''

        host = data['host']
        port = data['port']

        url = 'scgi://{}:{}'.format(host, port)

        client = rtorrent.SCGIServerProxy(url, encoding='utf-8')

        try:
            client.system.time()
            rTorrentSCGI.client = client
            return True
        except Exception as e:
            logging.error('rTorrent connection test failed.', exc_info=True)
            return str(e)

        return

    @staticmethod
    def add_torrent(data):
        ''' Adds torrent or magnet to rtorrent
        data: dict of torrrent/magnet information

        Adds label if set in config

        Returns dict {'response': True, 'downloadid': 'id'}
                     {'response': False, 'error': 'exception'}

        '''

        conf = core.CONFIG['Downloader']['Torrent']['rTorrentSCGI']

        if rTorrentSCGI.client is None:
            connected = rTorrentSCGI.test_connection(conf)
            if connected is not True:
                return {'response': False, 'error': connected}

        try:
            if conf['addpaused']:
                rTorrentSCGI.client.load(data['torrentfile'])
            else:
                rTorrentSCGI.client.load_start(data['torrentfile'])
            downloadid = Torrent.get_hash(data['torrentfile'])
            if conf['label'] and downloadid:
                rTorrentSCGI.client.d.set_custom1(downloadid, conf['label'])
                return {'response': True, 'downloadid': downloadid}
        except Exception as e:
            logging.error('Unable to send torrent to rTorrent', exc_info=True)
            return {'response': False, 'error': str(e)}


class rTorrentHTTP(object):

    client = None

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to rtorrent. Also used to create client object.
        data: dict of rtorrent server information

        Return True on success or str error message on failure
        '''

        address = data['address']
        user = data['user']
        password = data['pass']

        parts = urlparse(address)._asdict()
        if len(parts['netloc'].split(':')) == 1:
            port = 443 if parts['scheme'] == 'https' else 80
            parts['netloc'] = '{}:{}'.format(parts['netloc'], port)

        if user and password:
            url = '{}://{}:{}@{}/{}'.format(parts['scheme'], user, password, parts['netloc'], parts['path'])
        else:
            url = '{}://{}/{}'.format(parts['scheme'], parts['netloc'], parts['path'])

        context = None if core.CONFIG['Server']['verifyssl'] else core.NO_VERIFY

        client = xmlrpc.client.ServerProxy(url, context=context)

        try:
            client.system.time()
            rTorrentHTTP.client = client
            return True
        except Exception as e:
            logging.error('rTorrent connection test failed.', exc_info=True)
            return str(e)[1:-1]

        return

    @staticmethod
    def add_torrent(data):
        ''' Adds torrent or magnet to rtorrent
        data: dict of torrrent/magnet information

        Adds label if set in config

        Returns dict {'response': True, 'downloadid': 'id'}
                     {'response': False, 'error': 'exception'}

        '''

        conf = core.CONFIG['Downloader']['Torrent']['rTorrentHTTP']

        if rTorrentHTTP.client is None:
            connected = rTorrentHTTP.test_connection(conf)
            if connected is not True:
                return {'response': False, 'error': connected}

        try:
            if conf['addpaused']:
                rTorrentHTTP.client.load(data['torrentfile'])
            else:
                rTorrentHTTP.client.load_start(data['torrentfile'])

            downloadid = Torrent.get_hash(data['torrentfile'])
            if conf['label']:
                rTorrentHTTP.client.d.set_custom1(downloadid, conf['label'])
                return {'response': True, 'downloadid': downloadid}
        except Exception as e:
            logging.error('Unable to send torrent to ruTorrent HTTP', exc_info=True)
            return {'response': False, 'error': str(e)}

import logging
import core
import xmlrpc.client
from core.helpers import Torrent
import time
from urllib.parse import urlparse

logging = logging.getLogger(__name__)


client = None


def test_connection(data):
    ''' Tests connectivity to rtorrent. Also used to create client object.
    data: dict of rtorrent server information

    Return True on success or str error message on failure
    '''
    global client

    logging.info('Testing connection to rTorrent HTTP RPC plugin.')

    address = data['address']
    user = data['user']
    password = data['pass']

    parts = urlparse(address)._asdict()
    if len(parts['netloc'].split(':')) == 1:
        port = 443 if parts['scheme'] == 'https' else 80
        parts['netloc'] = '{}:{}'.format(parts['netloc'], port)

    if user and password:
        url = '{}://{}:{}@{}{}'.format(parts['scheme'], user, password, parts['netloc'], parts['path'])
    else:
        url = '{}://{}{}'.format(parts['scheme'], parts['netloc'], parts['path'])

    context = None if core.CONFIG['Server']['verifyssl'] else core.NO_VERIFY

    client = xmlrpc.client.ServerProxy(url, context=context)

    try:
        client.system.time()
        return True
    except Exception as e:
        logging.error('rTorrent connection test failed.', exc_info=True)
        return str(e)[1:-1]

    return


def add_torrent(data):
    ''' Adds torrent or magnet to rtorrent
    data: dict of torrrent/magnet information

    Adds label if set in config

    Returns dict {'response': True, 'downloadid': 'id'}
                 {'response': False, 'error': 'exception'}
    '''
    logging.info('Sending torrent {} to rTorrent HTTP RPC Plugin.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Torrent']['rTorrentHTTP']

    if client is None:
        connected = test_connection(conf)
        if connected is not True:
            return {'response': False, 'error': connected}

    try:
        downloadid = Torrent.get_hash(data['torrentfile'])

        if conf['addpaused']:
            client.load(data['torrentfile'])
        else:
            client.load_start(data['torrentfile'])

        if conf['label'] and downloadid:
            t = 0
            while t < 10:
                if downloadid in client.download_list():
                    client.d.set_custom1(downloadid, conf['label'])
                    return {'response': True, 'downloadid': downloadid}
                time.sleep(2)
                t += 1
            logging.error('Torrent hash ({}) not found in rTorrent after 10 seconds, cannot apply label.'.format(downloadid))
            return {'response': False, 'error': 'Torrent hash not found in rTorrent after 10 seconds, cannot apply label.'}
        else:
            return {'response': True, 'downloadid': downloadid}

    except Exception as e:
        logging.error('Unable to send torrent to rTorrent HTTP', exc_info=True)
        return {'response': False, 'error': str(e)[1:-1]}


def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    logging.info('Cancelling download # {} in rTorrent HTTP RPC Plugin.'.format(downloadid))

    conf = core.CONFIG['Downloader']['Torrent']['rTorrentHTTP']

    if client is None:
        connected = test_connection(conf)
        if connected is not True:
            return {'response': False, 'error': connected}

    try:
        mc = xmlrpc.client.MultiCall(client)
        mc.d.custom5.set(downloadid, '1')
        mc.d.delete_tied(downloadid)
        mc.d.erase(downloadid)
        mc()
        return True
    except Exception as e:
        logging.error('Unable to cancel download.', exc_info=True)
        return False

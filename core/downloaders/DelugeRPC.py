import logging
import re

from lib.deluge_client import DelugeRPCClient

import core

logging.getLogger('lib.deluge_client').setLevel(logging.CRITICAL)
logging = logging.getLogger(__name__)

label_fix = re.compile(r'[^a-z0-9_ -]')


def test_connection(config):
    ''' Tests connectivity to deluge daemon rpc
    config: dict of deluge server information

    Tests if we can open a socket to the rpc and creates DelugeRPC.client if successful

    Returns Bool True on success or str error message on failure
    '''

    logging.info('Testing connection to DelugeRPC')

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


def add_torrent(torrent):
    ''' Adds torrent or magnet to Deluge
    torrent: dict of torrrent/magnet information

    Returns dict {'response': True, 'download_id': 'id'}
                    {'response': False, 'error': 'exception'}

    '''

    logging.info('Sending torrent {} to DelugeRPC.'.format(torrent['title']))

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
            download_id = (client.call('core.add_torrent_url', torrent['torrentfile'], options) or b'').decode('utf-8')
        except Exception as e:
            logging.error('Unable to send torrent.', exc_info=True)
            return {'response': False, 'error': str(e)}
    else:
        return {'response': False, 'error': 'Invalid torrent type {}'.format(torrent['type'])}

    _set_label(download_id, conf['category'], client)

    return {'response': True, 'downloadid': download_id}


def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id
    Returns bool
    '''
    logging.info('Cancelling DelugeRPC download # {}'.format(downloadid))

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


def _set_label(torrent, label, client):
    ''' Sets label for download
    torrent: str hash of torrent to apply label
    label: str name of label to apply
    client: object DelugeRPCClient instance

    Returns Bool
    '''

    label = label_fix.sub('', label.lower())

    logging.info('Applying label {} to torrent {} in DelugeRPC.'.format(label, torrent))

    try:
        deluge_labels = client.call('label.get_labels')
    except Exception as e:
        logging.error('Unable to get labels from DelugeRPC.', exc_info=True)
        deluge_labels = []

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

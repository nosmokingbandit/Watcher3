import logging

from lib import transmissionrpc

import core

logging = logging.getLogger(__name__)


def test_connection(data):
    ''' Tests connectivity to Transmission
    data: dict of Transmission server information

    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to Transmission.')

    host = data['host']
    port = data['port']
    user = data['user']
    password = data['pass']

    try:
        client = transmissionrpc.Client(host, port, user=user, password=password)
        if type(client.rpc_version) == int:
            return True
        else:
            logging.warning('Unable to connect to TransmissionRPC.')
            return 'Unable to connect.'
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Unable to connect to TransmissionRPC.', exc_info=True)
        return '{}.'.format(e)


def add_torrent(data):
    ''' Adds torrent or magnet to Transmission
    data: dict of torrrent/magnet information

    Adds torrents to /default/path/<category>

    Returns dict {'response': True, 'downloadid': 'id'}
                    {'response': False', 'error': 'exception'}

    '''

    logging.info('Sending torrent {} to Transmission.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Torrent']['Transmission']

    host = conf['host']
    port = conf['port']
    user = conf['user']
    password = conf['pass']

    client = transmissionrpc.Client(host, port, user=user, password=password)

    url = data['torrentfile']
    paused = conf['addpaused']
    bandwidthPriority = conf['priority']
    category = conf['category']

    priority_keys = {
        'Low': '-1',
        'Normal': '0',
        'High': '1'
    }

    bandwidthPriority = priority_keys[conf['priority']]

    download_dir = None
    if category:
        d = client.get_session().__dict__['_fields']['download_dir'][0]
        d_components = d.split('/')
        d_components.append(category)

        download_dir = '/'.join(d_components)

    try:
        download = client.add_torrent(url, paused=paused, bandwidthPriority=bandwidthPriority, download_dir=download_dir, timeout=30)
        downloadid = download.hashString
        logging.info('Torrent sent to TransmissionRPC - downloadid {}'.format(downloadid))
        return {'response': True, 'downloadid': downloadid}
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Unable to send torrent to TransmissionRPC.', exc_info=True)
        return {'response': False, 'error': str(e)}


def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    logging.info('Cancelling download # {} in Transmission.'.format(downloadid))

    conf = core.CONFIG['Downloader']['Torrent']['Transmission']

    host = conf['host']
    port = conf['port']
    user = conf['user']
    password = conf['pass']

    client = transmissionrpc.Client(host, port, user=user, password=password)

    try:
        client.remove_torrent([downloadid], delete_data=True)
        return True
    except Exception as e:
        logging.error('Unable to cancel download.', exc_info=True)
        return False

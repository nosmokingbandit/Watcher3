import logging
import json

import core
from core.helpers import Torrent, Url

logging = logging.getLogger(__name__)


cookie = None


def _send(method, post_data=None):
    ''' Sends API request to QBittorrent
    method (str): name of method to call. *must* include category (ie 'query/preferences')
    post_data (dict): post data to send with request    <optional>

    Returns str text response from QBit
    '''
    global cookie

    conf = core.CONFIG['Downloader']['Torrent']['QBittorrent']

    if not cookie:
        r = _login('{}:{}/'.format(conf['host'], conf['port']), conf['user'], conf['pass'])
        if r is not True:
            logging.error('Unable to connect to QBittorrent: {}'.format(r))
            return False

    url = '{}:{}/{}'.format(conf['host'], conf['port'], method)

    try:
        response = Url.open(url, post_data=post_data, headers={'cookie': cookie})
    except Exception as e:
        logging.error('Unable to contact QBittorrent API.', exc_info=True)
        raise APIConnectionError(response.status_code, response.reason)

    if response.status_code == 403:
        logging.info('QBittorrent request unauthorized.')
        cookie = None
        u = '{}:{}/'.format(conf['host'], conf['port'])
        if _login(u, conf['user'], conf['pass']) is not True:
            raise APIConnectionError('403', 'Unable to log in to QBittorrent.')
        else:
            try:
                response = Url.open(url, post_data=post_data, headers={'cookie': cookie})
            except Exception as e:
                logging.error('Unable to contact QBittorrent API.', exc_info=True)
                raise APIConnectionError(response.status_code, response.reason)
    elif response.status_code != 200:
        logging.error('QBittorrent API call failed: {}'.format(response.reason))
        raise APIConnectionError(response.status_code, response.reason)

    return response.text


def test_connection(data):
    ''' Tests connectivity to qbittorrent
    data: dict of qbittorrent server information

    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to QBittorrent.')

    url = '{}:{}/'.format(data['host'], data['port'])

    return _login(url, data['user'], data['pass'])


def add_torrent(data):
    ''' Adds torrent or magnet to qbittorrent
    data: dict of torrrent/magnet information

    Adds torrents to default/path/<category>

    Returns dict {'response': True, 'download_id': 'id'}
                    {'response': False, 'error': 'exception'}

    '''

    logging.info('Sending torrent {} to QBittorrent.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Torrent']['QBittorrent']

    host = conf['host']
    port = conf['port']
    base_url = '{}:{}/'.format(host, port)

    download_dir = _get_download_dir(base_url)

    if download_dir is None:
        return {'response': False, 'error': 'Unable to get path information.'}
    # if we got download_dir we can connect.

    post_data = {'urls': data['torrentfile'],
                 'savepath': '{}{}'.format(download_dir, conf['category']),
                 'category': conf['category']
                 }

    try:
        _send('command/download', post_data=post_data)
        downloadid = Torrent.get_hash(data['torrentfile'])
        return {'response': True, 'downloadid': downloadid}
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('QBittorrent command/download failed.', exc_info=True)
        return {'response': False, 'error': str(e)}


def _get_download_dir(base_url):
    logging.debug('Getting default download dir for QBittorrent.')

    try:
        response = _send('query/preferences')
        return json.loads(response)['save_path']
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('QBittorrent query/preferences failed.', exc_info=True)
        return None


def _login(url, username, password):
    global cookie

    logging.info('Attempting to log in to QBittorrent.')

    post_data = {'username': username, 'password': password}

    url = '{}login'.format(url)
    try:
        response = Url.open(url, post_data=post_data)
        cookie = response.headers.get('Set-Cookie')

        if response.text == 'Ok.':
            logging.info('Successfully connected to QBittorrent.')
            return True
        elif response.text == 'Fails.':
            logging.warning('Incorrect usename or password QBittorrent.')
            return 'Incorrect usename or password'
        else:
            logging.warning(response.text)
            return response.text
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('qbittorrent test_connection', exc_info=True)
        return '{}.'.format(str(e))


def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    logging.info('Cancelling download # {} in QBittorrent.'.format(downloadid))

    try:
        _send('command/deletePerm', post_data={'hashes': downloadid.lower()})
        return True
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('QBittorrent query/preferences failed.', exc_info=True)
        return None


class APIConnectionError(Exception):
    ''' Raised when a timed task is in conflict with itself '''
    def __init__(self, status_code, reason):
        self.msg = 'QBittorrent API request error {}: {}'.format(status_code, reason)

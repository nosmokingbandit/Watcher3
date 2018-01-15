import logging
import json
import re
import core
from core.helpers import Torrent, Url

cookie = None
command_id = 0

label_fix = re.compile('[^a-z0-9_-]')

headers = {'Content-Type': 'application/json', 'User-Agent': 'Watcher'}


logging = logging.getLogger(__name__)


def test_connection(data):
    ''' Tests connectivity to deluge web client
    data: dict of deluge server information


    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to Deluge Web UI.')

    host = data['host']
    port = data['port']
    password = data['pass']

    url = '{}:{}/json'.format(host, port)

    return _login(url, password)


def add_torrent(data):
    ''' Adds torrent or magnet to deluge web api
    data (dict): torrrent/magnet information

    Adds torrents to default/path/<category>

    Returns dict ajax-style response
    '''
    global command_id

    logging.info('Sending torrent {} to Deluge Web UI.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']

    host = conf['host']
    port = conf['port']
    url = '{}:{}/json'.format(host, port)

    priority_keys = {
        'Normal': 0,
        'High': 128,
        'Max': 255
    }

    if cookie is None:
        if _login(url, conf['pass']) is not True:
            return {'response': False, 'error': 'Incorrect usename or password.'}

    download_dir = _get_download_dir(url)

    if not download_dir:
        return {'response': False, 'error': 'Unable to get path information.'}
    # if we got download_dir we can connect.

    download_dir = '{}/{}'.format(download_dir, conf['category'])

    # if file is a torrent, have deluge download it to a tmp dir
    if data['type'] == 'torrent':
        tmp_torrent_file = _get_torrent_file(data['torrentfile'], url)
        if tmp_torrent_file['response'] is True:
            torrent = {'path': tmp_torrent_file['torrentfile'], 'options': {}}
        else:
            return {'response': False, 'error': tmp_torrent_file['error']}
    else:
        torrent = {'path': data['torrentfile'], 'options': {}}

    torrent['options']['add_paused'] = conf['addpaused']
    torrent['options']['download_location'] = download_dir
    torrent['options']['priority'] = priority_keys[conf['priority']]

    command = {'method': 'web.add_torrents',
               'params': [[torrent]],
               'id': command_id
               }
    command_id += 1

    post_data = json.dumps(command)
    headers['cookie'] = cookie

    try:
        response = Url.open(url, post_data=post_data, headers=headers)
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

    _set_label(downloadid, conf['category'], url)

    return {'response': True, 'downloadid': downloadid}


def _set_label(torrent, label, url):
    ''' Sets label for download
    torrent: str hash of torrent to apply label
    label: str name of label to apply
    url: str url of deluge web interface

    Returns bool
    '''
    global command_id

    label = label_fix.sub('', label.lower()).replace(' ', '')

    logging.info('Applying label {} to torrent {} in Deluge Web UI.'.format(label, torrent))

    command = {'method': 'label.get_labels',
               'params': [],
               'id': command_id
               }
    command_id += 1

    try:
        response = Url.open(url, post_data=json.dumps(command), headers=headers).text
        deluge_labels = json.loads(response).get('result') or []
    except Exception as e:
        logging.error('Unable to get labels from Deluge Web UI.', exc_info=True)
        return False

    if label not in deluge_labels:
        logging.info('Adding label {} to Deluge.'.format(label))
        command = {'method': 'label.add',
                   'params': [label],
                   'id': command_id
                   }
        command_id += 1
        try:
            sc = Url.open(url, post_data=json.dumps(command), headers=headers).status_code
            if sc != 200:
                logging.error('Deluge Web UI response {}.'.format(sc))
                return False
        except Exception as e:
            logging.error('Delugeweb get_labels.', exc_info=True)
            return False
    try:
        command = {'method': 'label.set_torrent',
                   'params': [torrent.lower(), label],
                   'id': command_id
                   }
        command_id += 1
        sc = Url.open(url, post_data=json.dumps(command), headers=headers).status_code
        if sc != 200:
            logging.error('Deluge Web UI response {}.'.format(sc))
            return False
    except Exception as e:
        logging.error('Delugeweb set_torrent.', exc_info=True)
        return False

    return True


def _get_torrent_file(torrent_url, deluge_url):
    global command_id

    command = {'method': 'web.download_torrent_from_url',
               'params': [torrent_url],
               'id': command_id
               }
    command_id += 1
    post_data = json.dumps(command)
    headers['cookie'] = cookie
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


def _get_download_dir(url):
    global command_id

    logging.debug('Getting default download dir from Deluge Web UI.')

    command = {'method': 'core.get_config_value',
               'params': ['download_location'],
               'id': command_id
               }
    command_id += 1

    post_data = json.dumps(command)

    headers['cookie'] = cookie

    try:
        response = Url.open(url, post_data=post_data, headers=headers)
        response = json.loads(response.text)
        return response['result']
    except Exception as e:
        logging.error('delugeweb get_download_dir', exc_info=True)
        return {'response': False, 'error': str(e)}


def _login(url, password):
    global command_id
    global cookie

    logging.info('Logging in to Deluge Web UI.')

    command = {'method': 'auth.login',
               'params': [password],
               'id': command_id
               }
    command_id += 1

    post_data = json.dumps(command)

    try:
        response = Url.open(url, post_data=post_data, headers=headers)
        cookie = response.headers.get('Set-Cookie')

        if cookie is None:
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


def cancel_download(downloadid):
    global command_id

    logging.info('Cancelling download {} in Deluge Web UI'.format(downloadid))

    conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']

    host = conf['host']
    port = conf['port']
    url = '{}:{}/json'.format(host, port)

    if cookie is None:
        _login(url, conf['pass'])

    command = {'method': 'core.remove_torrent',
               'params': [downloadid.lower(), True],
               'id': command_id
               }
    command_id += 1

    post_data = json.dumps(command)

    headers['cookie'] = cookie

    try:
        response = Url.open(url, post_data=post_data, headers=headers)
        response = json.loads(response.text)
        return response['result']
    except Exception as e:
        logging.error('delugeweb get_download_dir', exc_info=True)
        return {'response': False, 'error': str(e)}

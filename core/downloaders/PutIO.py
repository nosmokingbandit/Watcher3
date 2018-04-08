import logging
import core
import json
from core.helpers import Url

from lib import putiopy

logging = logging.getLogger(__name__)

url_base = "https://api.put.io/v2/{}?oauth_token={}"


def requires_oauth(func):
    ''' Decorator to check if oauthtoken exists before calling actual method
    '''
    def decor(*args, **kwargs):
        if not core.CONFIG['Downloader']['Torrent']['PutIO']['oauthtoken']:
            return {'response': False, 'error': 'No OAuth Token. Create OAuth token on Put.io and enter in settings.'}
        return func(*args, **kwargs)
    return decor


def test_connection(data):
    ''' Tests connectivity to Put.IO
    data: dict of Put.IO server information

    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to Put.IO.')


@requires_oauth
def add_torrent(data):
    ''' Adds torrent or magnet to Put.IO
    data: dict of torrrent/magnet information

    Adds torrents to /default/path/<category>

    Returns dict {'response': True, 'download_id': 'id'}
                    {'response': False', 'error': 'exception'}

    '''

    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    url = url_base.format('transfers/add', conf['oauthtoken'])

    post_data = {'url': data['torrent_file']}

    if conf['saveparentid']:
        post_data['save_parent_id'] = conf['saveparentid']
    if conf['enablepostprocessing']:
        post_data['callback_url'] = '{}/api?apikey={}&mode=putio'.format(conf['externaladdress'])

    response = Url.open(url, post_data=post_data)

    logging.debug(response)


@requires_oauth
def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    url = url_base.format('transfers/cancel', conf['oauthtoken'])

    post_data = {'id': downloadid}

    response = Url.open(url, post_data=post_data)

    if json.loads(response).gets('status') == 'OK':
        return True
    else:
        return False


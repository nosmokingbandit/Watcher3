import logging
import core
import json
from core.helpers import Url

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

    if not core.CONFIG['Downloader']['Torrent']['PutIO']['oauthtoken']:
        return 'No Application Token. Create Application token and enter in settings.'

    response = Url.open(url_base.format('account/info', core.CONFIG['Downloader']['Torrent']['PutIO']['oauthtoken']))

    if response.status_code != 200:
        return '{}: {}'.format(response.status_code, response.reason)

    response = json.loads(response.text)
    if response['status'] != 'OK':
        return response['error_message']
    else:
        return True


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
        post_data['callback_url'] = '{}/postprocessing/putio_process?apikey={}'.format(conf['externaladdress'], core.CONFIG['Server']['apikey'])

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


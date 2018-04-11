import logging
import core
import json
import os
from core.helpers import Url

logging = logging.getLogger(__name__)

url_base = "https://api.put.io/v2/{}?oauth_token={}"


def requires_oauth(func):
    ''' Decorator to check if oauthtoken exists before calling actual method
    '''
    def decor(*args, **kwargs):
        if not core.CONFIG['Downloader']['Torrent']['PutIO']['oauthtoken']:
            logging.debug('Cannot execute Put.IO method -- no OAuth Token in config.')
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
        logging.debug('Cannot execute Put.IO method -- no OAuth Token in config.')
        return 'No Application Token. Create Application token and enter in settings.'

    response = Url.open(url_base.format('account/info', core.CONFIG['Downloader']['Torrent']['PutIO']['oauthtoken']))

    if response.status_code != 200:
        return '{}: {}'.format(response.status_code, response.reason)

    response = json.loads(response.text)
    if response['status'] != 'OK':
        logging.debug('Cannot connect to Put.IO: {}'.format(response['error_message']))
        return response['error_message']
    else:
        return True


@requires_oauth
def add_torrent(data):
    ''' Adds torrent or magnet to Put.IO
    data: dict of torrrent/magnet information

    Adds torrents to /default/path/<category>

    Returns dict {'response': True, 'downloadid': 'id'}
                    {'response': False', 'error': 'exception'}

    '''

    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    url = url_base.format('transfers/add', conf['oauthtoken'])

    post_data = {'url': data['torrentfile']}

    if conf['directory']:
        post_data['save_parent_id'] = conf['directory']
    if conf['postprocessingenabled']:
        post_data['callback_url'] = '{}/postprocessing/putio_process?apikey={}'.format(conf['externaladdress'], core.CONFIG['Server']['apikey'])

    try:
        response = Url.open(url, post_data=post_data)
    except Exception as e:
        logging.warning('Cannot send download to Put.io', exc_info=True)
        return {'response': False, 'error': str(e)}

    if response.status_code != 200:
        return {'response': False, 'error': '{}: {}'.format(response.status_code, response.reason)}

    try:
        response = json.loads(response.text)
        downloadid = response['transfer']['id']
    except Exception as e:
        logging.warning('Unexpected response from Put.io', exc_info=True)
        return {'response': False, 'error': 'Invalid JSON response from Put.IO'}

    return {'response': True, 'downloadid': downloadid}


@requires_oauth
def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    url = url_base.format('transfers/cancel', conf['oauthtoken'])

    try:
        response = Url.open(url, post_data={'id': downloadid})
    except Exception as e:
        logging.warning('Unable to cancel Put.io download.', exc_info=True)
        return {'response': False, 'error': str(e)}

    try:
        if json.loads(response.text).get('status') == 'OK':
            return True
        else:
            logging.warning('Unable to cancel Put.io download: {}'.format(response))
            return False
    except Exception as e:
        logging.warning('Unable to cancel Put.io download', exc_info=True)
        return False


@requires_oauth
def download(_id):
    ''' Gets link to file from Put.IO
    _id (str/int): ID to download, can be file or dir

    Downloads all files in putio dir

    Returns dict
    '''
    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    try:
        response = Url.open(url_base.format('files/{}'.format(_id), conf['oauthtoken']))
    except Exception as e:
        return {'response': False, 'error': str(e)}

    try:
        response = json.loads(response.text)
        f_data = response['file']
    except Exception as e:
        return {'response': False, 'error': 'Invalid json response from Put.io'}

    if f_data['content_type'] == 'application/x-directory':
        file_list = _read_dir(f_data['id'], conf['oauthtoken'])
    else:
        file_list = [f_data]

    download_dir = os.path.join(conf['downloaddirectory'], f_data['name'])

    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
        except Exception as e:
            logging.error('Cannot create download dir', exc_info=True)
            return {'response': False, 'error': 'Cannot create download dir. {}'.format(str(e))}
    else:
        logging.warning('Download dir exists, existing files may be overwritten.')

    download_results = []
    for i in file_list:
        download_results.append(_download_file(i, download_dir, conf['oauthtoken']))

    logging.info('Download from Put.io finished:')
    logging.info(json.dumps(download_results, indent=2))

    return {'response': True, 'files': download_results, 'path': download_dir}


@requires_oauth
def delete(file_id):
    ''' Deletes file from Put.IO
    file_id (str): Put.IO id # for file or folder

    Returns bool
    '''
    logging.info('Deleting file {} on Put.IO'.format(file_id))
    conf = core.CONFIG['Downloader']['Torrent']['PutIO']

    url = url_base.format('files/delete', conf['oauthtoken'])

    try:
        response = Url.open(url, post_data={'file_ids': file_id})
    except Exception as e:
        logging.warning('Could not delete files on Put.io', exc_info=True)

    try:
        response = json.loads(response.text)
    except Exception as e:
        logging.warning('Unexpected response from Put.IO', exc_info=True)

    return response.get('status') == 'OK'


def _download_file(f_data, directory, token):
    ''' Downloads file to local dir
    f_data (dict): Putio file metadata
    directory (str): Path in which to save file
    token (str): oauth token

    Downloads file to local dir

    Returns dict
    '''

    try:
        response = Url.open(url_base.format('files/{}/download'.format(f_data['id']), token), stream=True)
    except Exception as e:
        logging.error('Unable to download file from Put.io', exc_info=True)
        return {'success': False, 'name': f_data['name'], 'error': str(e)}

    target_file = os.path.join(directory, f_data['name'])
    try:
        with open(target_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        return {'success': False, 'name': f_data['name'], 'error': str(e)}

    return {'success': True, 'name': f_data['name'], 'location': target_file}


def _read_dir(dir_id, token):
    ''' Recursively reads dir for all files
    dir_id (str/int): Put.io directory #

    Returns list of dicts
    '''

    files = []

    try:
        response = Url.open(url_base.format('files/list', token) + '&parent_id={}'.format(dir_id))
    except Exception as e:
        logging.warning('Unable to read files on Put.io', exc_info=True)
        return []

    try:
        contents = json.loads(response.text)['files']
    except Exception as e:
        logging.warning('Unexpected response from Put.io')
        return []

    for i in contents:
        if i['content_type'] == 'application/x-directory':
            files += _read_dir(i['id'], token)
        else:
            files.append(i)

    return files

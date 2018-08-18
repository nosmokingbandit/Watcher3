import logging
import json
import core
from core.helpers import Url
from urllib.parse import quote as urlquote

cookie = None

logging = logging.getLogger(__name__)

errors = {100: 'Unknown error',
          101: 'Invalid parameter',
          102: 'The requested API does not exist',
          103: 'The requested method does not exist',
          104: 'The requested version does not support the functionality',
          105: 'The logged in session does not have permission',
          106: 'Session timeout',
          107: 'Session interrupted by duplicate login'
          }


def auth_required(func):
    ''' Decorator to check login before executing method
    '''
    def decor(*args, **kwargs):
        global cookie
        if cookie is None:
            conf = core.CONFIG['Downloader']['Torrent']['DownloadStation']
            url_base = '{}:{}'.format(conf['host'], conf['port'])

            login = _login(url_base, conf['account'], conf['pass'])
            if login is not True:
                return {'response': False, 'error': login}

        return func(*args, **kwargs)
    return decor


def test_connection(data):
    ''' Tests connectivity to DownloadStation
    data: dict of DownloadStation server information

    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to DownloadStation')

    url = '{}:{}'.format(data['host'], data['port'])

    return _login(url, data['account'], data['pass'])


def _login(url, account, password):
    ''' Log in to Synology to access application api
    url (str): host:port of SynologyOS
    account (str): user's account name
    password (str): user's password. Pass empty string if no password for user

    Sets global cookie to response sid

    Returns bool True or str error message
    '''

    global cookie

    logging.info('Logging in to Synology')

    url = '{}/webapi/auth.cgi?api=SYNO.API.Auth&version=2&method=login&account={}&passwd={}&session=DownloadStation&format=cookie'.format(url, account, password)

    try:
        response = Url.open(url)

        if response.status_code != 200:
            cookie = None
            return '{}: {}'.format(response.status_code, response.reason)

        response = json.loads(response.text)
        if not response['success']:
            cookie = None
            return 'Invalid Credentials'
        else:
            cookie = response['data']['sid']
            return True
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        cookie = None
        logging.error('Synology login failed', exc_info=True)
        return '{}.'.format(e)


@auth_required
def add_nzb(data):
    ''' Adds nzb to DownloadStation
    data (dict): nzb information

    Adds torrents to default/path/<category>

    Returns dict ajax-style response
    '''

    logging.info('Sending nzb {} to DownloadStation.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Usenet']['DownloadStation']
    url_base = '{}:{}'.format(conf['host'], conf['port'])

    url = '{}/webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=2&method=create&uri={}&destination={}&_sid={}'.format(url_base, urlquote(data['guid']), conf['destination'], cookie)

    try:
        response = Url.open(url)

        if response.status_code != 200:
            return {'response': False, 'error': '{}: {}'.format(response.status_code, response.reason)}
        else:
            response = json.loads(response.text)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('DownloadStation add_torrent', exc_info=True)
        return {'response': False, 'error': str(e)}

    if not response['success']:
        return {'response': False, 'error': errors.get(response['error'], errors[100])}

    return {'response': True, 'downloadid': data['guid']}


@auth_required
def add_torrent(data):
    ''' Adds torrent or magnet to DownloadStation
    data (dict): torrrent/magnet information

    Adds torrents to default/path/<category>

    Returns dict ajax-style response
    '''

    logging.info('Sending torrent {} to DownloadStation.'.format(data['title']))

    conf = core.CONFIG['Downloader']['Torrent']['DownloadStation']
    url_base = '{}:{}'.format(conf['host'], conf['port'])

    url = '{}/webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=2&method=create&uri={}&destination={}&_sid={}'.format(url_base, urlquote(data['torrentfile']), conf['destination'], cookie)

    try:
        response = Url.open(url)

        if response.status_code != 200:
            return {'response': False, 'error': '{}: {}'.format(response.status_code, response.reason)}
        else:
            response = json.loads(response.text)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('DownloadStation add_torrent', exc_info=True)
        return {'response': False, 'error': str(e)}

    if not response['success']:
        return {'response': False, 'error': errors.get(response['error'], errors[100])}

    return {'response': True, 'downloadid': data['torrentfile']}


def get_task_id(url_base, uri):
    ''' Gets task_id from DownloadStation
    url_base (str): host:port of DownloadStation
    uri (str): uri used to create download

    Can return empty string if something breaks

    Returns str
    '''

    url = '{}/webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=2&method=list&additional=detail&_sid={}'.format(url_base, cookie)

    try:
        response = Url.open(url)

        if response.status_code != 200:
            return '{}: {}'.format(response.status_code, response.reason)
        else:
            response = json.loads(response.text)

        for i in response['data']['tasks']:
            if i['additional']['detail']['uri'] == uri:
                return i['id']
    except Exception as e:  # noqa
        return ''


@auth_required
def cancel_download(downloadid):

    conf = core.CONFIG['Downloader']['Torrent']['DownloadStation']
    url_base = '{}:{}'.format(conf['host'], conf['port'])

    task_id = get_task_id(url_base, downloadid)
    if task_id == '':
        logging.error('Unable to get task_id from DownloadStation')
        return False

    url = '{}/webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1&method=delete&id={}&force_complete=false&_sid={}'.format(url_base, task_id, cookie)

    try:
        response = Url.open(url)

        if response.status_code != 200:
            return '{}: {}'.format(response.status_code, response.reason)
        else:
            response = json.loads(response.text)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:  # noqa
        logging.error('DownloadStation cancel_download', exc_info=True)
        return False

    if response['data'][0]['error'] != 0:
        logging.error('Cannot cancel DownloadStation download: {}'.format(errors.get(response['data'][0]['error'], errors[100])))
        return False

    return True

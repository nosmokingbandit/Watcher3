import logging
from xmlrpc.client import ServerProxy

import core

logging = logging.getLogger(__name__)


def test_connection(data):
    ''' Tests connectivity to Nzbget
    :para data: dict of nzbget server information

    Tests if we can get nzbget's version using server info in 'data'

    Return True on success or str error message on failure
    '''

    logging.info('Testing connection to NZBGet.')

    host = data['host']
    port = data['port']
    user = data['user']
    passw = data['pass']

    if not host.startswith('http'):
        url = 'http://{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)
    else:
        url = '{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)

    nzbg_server = ServerProxy(url)

    try:
        nzbg_server.version()
        return True
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Nzbget test_connection', exc_info=True)
        return '{}.'.format(e)


def add_nzb(nzb):
    ''' Adds nzb file to nzbget to download
    :param nzb: dict of nzb information

    Returns str response from server
    '''

    logging.info('Sending NZB {} to NZBGet.'.format(nzb['title']))

    conf = core.CONFIG['Downloader']['Usenet']['NzbGet']

    host = conf['host']
    port = conf['port']
    user = conf['user']
    passw = conf['pass']

    if not host.startswith('http'):
        url = 'http://{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)
    else:
        url = '{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)

    nzbg_server = ServerProxy(url)

    filename = '{}.nzb'.format(nzb['title'])
    contenturl = nzb['guid']
    category = conf['category']
    priority_keys = {
        'Very Low': -100,
        'Low': -50,
        'Normal': 0,
        'High': 50,
        'Very High': 100,
        'Forced': 900
    }
    priority = priority_keys[conf['priority']]
    if conf['addpaused']:
        paused = True
    else:
        paused = False
    dupekey = nzb['imdbid']
    dupescore = nzb['score']
    dupemode = 'All'

    try:
        response = nzbg_server.append(filename, contenturl, category, priority, False, paused, dupekey, dupescore, dupemode)
        logging.info('NZB sent to NZBGet - downloadid {}'.format(response))
        return {'response': True, 'downloadid': response}
    except Exception as e:
        logging.error('Unable to add NZB to NZBGet.')
        return {'response': False, 'error': str(e)}


def cancel_download(downloadid):
    ''' Cancels download in client
    downloadid: int download id

    Returns bool
    '''
    logging.info('Cancelling download # {} in NZBGet.'.format(downloadid))

    conf = core.CONFIG['Downloader']['Usenet']['NzbGet']

    host = conf['host']
    port = conf['port']
    user = conf['user']
    passw = conf['pass']

    if not host.startswith('http'):
        url = 'http://{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)
    else:
        url = '{}:{}/{}:{}/xmlrpc'.format(host, port, user, passw)

    nzbg_server = ServerProxy(url)

    try:
        return nzbg_server.editqueue('GroupDelete', 0, '', [int(downloadid)])
    except Exception as e:
        logging.error('Unable to cancel download.', exc_info=True)
        return False

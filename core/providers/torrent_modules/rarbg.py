import datetime
import core
import logging
import time
from core.helpers import Url
import json

logging = logging.getLogger(__name__)

'''
https://torrentapi.org/apidocs_v2.txt

This api is limited to one request every 2 seconds.
'''

timeout = None
_api_token = None
_token_timeout = datetime.datetime.now()


def _token():
    ''' Gets/sets token and monitors token timeout

    Returns str rarbg token
    '''
    global _api_token
    global _token_timeout

    if not _api_token:
        _api_token = _get_token()
    else:
        now = datetime.datetime.now()
        if (now - _token_timeout).total_seconds() > 900:
            _api_token = _get_token()
            _token_timeout = now
    return _api_token


def search(imdbid, term):
    ''' Search api for movie
    imdbid (str): imdb id #

    Returns list of dicts of parsed releases
    '''
    global timeout

    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Performing backlog search on Rarbg for {}.'.format(imdbid))
    if timeout:
        now = datetime.datetime.now()
        while timeout > now:
            time.sleep(1)
            now = datetime.datetime.now()

    try:
        url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=search&search_imdb={}&category=movies&format=json_extended&app_id=Watcher'.format(_token(), imdbid)

        timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

        if proxy_enabled and core.proxy.whitelist('https://www.torrentapi.org') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        results = json.loads(response).get('torrent_results')
        if results:
            return _parse(results, imdbid=imdbid)
        else:
            logging.info('Nothing found on Rarbg')
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Rarbg search failed.', exc_info=True)
        return []


def get_rss():
    ''' Gets latest rss feed from api

    Returns list of dicts of parsed releases
    '''
    global timeout

    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Fetching latest RSS from ')
    if timeout:
        now = datetime.datetime.now()
        while timeout > now:
            time.sleep(1)
            now = datetime.datetime.now()

    try:
        url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=list&category=movies&format=json_extended&app_id=Watcher'.format(_token())
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

        if proxy_enabled and core.proxy.whitelist('https://www.torrentapi.org') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        results = json.loads(response).get('torrent_results')
        if results:
            return _parse(results)
        else:
            logging.info('Nothing found in Rarbg RSS.')
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Rarbg RSS fetch failed.', exc_info=True)
        return []


def _get_token():
    ''' Get api access token

    Returns str or None
    '''
    logging.info('Getting RarBG access token.')
    url = 'https://www.torrentapi.org/pubapi_v2.php?get_token=get_token&app_id=Watcher'

    try:
        result = json.loads(Url.open(url).text)
        token = result.get('token')
        return token
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Failed to get Rarbg token.', exc_info=True)
        raise RarbgTokenError(str(e))


def _parse(results, imdbid=None):
    ''' Parse api response
    results (list): dicts of releases

    Returns list of dicts
    '''

    logging.info('Parsing {} Rarbg results.'.format(len(results)))
    item_keep = ('size', 'pubdate', 'title', 'indexer', 'info_link', 'guid', 'torrentfile', 'resolution', 'type', 'seeders')

    parsed_results = []

    for result in results:
        result['indexer'] = 'Rarbg'
        result['info_link'] = result['info_page']
        result['torrentfile'] = result['download']
        result['guid'] = result['download'].split('&')[0].split(':')[-1]
        result['type'] = 'magnet'
        result['pubdate'] = None

        result = {k: v for k, v in result.items() if k in item_keep}

        result['imdbid'] = imdbid or result.get('episode_info', {}).get('imdb')
        result['status'] = 'Available'
        result['score'] = 0
        result['downloadid'] = None
        result['freeleech'] = 0
        result['download_client'] = None
        parsed_results.append(result)

    logging.info('Found {} results from '.format(len(parsed_results)))
    return parsed_results


class RarbgTokenError(Exception):
    ''' Raised when a Rarbg token cannot be retrieved '''
    def __init__(self, msg=None):
        self.msg = msg if msg else 'Failed to retrieve new token from Rarbg\'s torrentapi.org.'

import core
import logging
from core.helpers import Url
import json

logging = logging.getLogger(__name__)


def search(imdbid, term):
    ''' Search api for movie
    imdbid (str): imdb id #

    Returns list of dicts of parsed releases
    '''

    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']
    username = core.CONFIG['Indexers']['PrivateTorrent']['danishbits']['username']
    passkey = core.CONFIG['Indexers']['PrivateTorrent']['danishbits']['passkey']

    logging.info('Performing backlog search on DanishBits for {}.'.format(imdbid))

    try:
        url = 'https://danishbits.org/couchpotato.php?user={}&passkey={}&imdbid={}'.format(username, passkey, imdbid)

        if proxy_enabled and core.proxy.whitelist('https://danishbits.org') is True:
            response = Url.open(url, proxy_bypass=True, expose_user_agent=True).text
        else:
            response = Url.open(url, expose_user_agent=True).text

        responseobject = json.loads(response)
        results = responseobject.get('results')

        if results:
            return _parse(results, imdbid=imdbid)
        else:
            logging.info('Nothing found on DanishBits')
            errormsg = responseobject.get('error')
            if errormsg:
                logging.info('Error message: {}'.format(errormsg))
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('DanishBits search failed.', exc_info=True)
        return []


def _parse(results, imdbid=None):
    ''' Parse api response
    results (list): dicts of releases

    Returns list of dicts
    '''

    logging.info('Parsing {} DanishBits results.'.format(len(results)))
    parsed_results = []

    for result in results:
        parsed_result = {}
        parsed_result['indexer'] = 'DanishBits'
        parsed_result['info_link'] = result['details_url']
        parsed_result['torrentfile'] = result['download_url']
        parsed_result['guid'] = result['torrent_id']
        parsed_result['type'] = 'torrent'
        parsed_result['pubdate'] = result['publish_date']
        parsed_result['seeders'] = result['seeders']
        parsed_result['size'] = result['size'] * 1000000

        parsed_result['imdbid'] = result['imdb_id']
        parsed_result['status'] = 'Available'
        parsed_result['score'] = 0
        parsed_result['downloadid'] = None
        parsed_result['freeleech'] = True
        parsed_result['download_client'] = None
        parsed_result['title'] = result['release_name']
        parsed_results.append(parsed_result)

    logging.info('Found {} results from DanishBits'.format(len(parsed_results)))
    return parsed_results

import core
import logging
from core.helpers import Url
import json
import xml.etree.cElementTree as ET

logging = logging.getLogger(__name__)


def search(imdbid, term):
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Performing backlog search on YTS for {}.'.format(imdbid))

    url = 'https://yts.ag/api/v2/list_movies.json?limit=1&query_term={}'.format(imdbid)

    try:
        if proxy_enabled and core.proxy.whitelist('https://www.yts.ag') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            r = json.loads(response)
            if r['data']['movie_count'] < 1:
                return []
            else:
                return _parse(r['data']['movies'][0], imdbid, term)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('YTS search failed.', exc_info=True)
        return []


def get_rss():
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Fetching latest RSS from YTS.')

    url = 'https://yts.ag/rss/0/all/all/0'

    try:
        if proxy_enabled and core.proxy.whitelist('https://www.yts.ag') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            return _parse_rss(response)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('YTS RSS fetch failed.', exc_info=True)
        return []


def _parse(movie, imdbid, title):
    logging.info('Parsing {} YTS results.'.format(len(movie['torrents'])))

    results = []
    for i in movie['torrents']:
        result = {}
        if i['quality'] == '3D':
            i['quality'] = '1080P.3D'
        try:
            result['score'] = 0
            result['size'] = i['size_bytes']
            result['status'] = 'Available'
            result['pubdate'] = i['date_uploaded']
            result['title'] = '{}.Bluray.{}.YTS'.format(title, i['quality'])
            result['imdbid'] = imdbid
            result['indexer'] = 'YTS'
            result['info_link'] = 'https://ag/movie/{}'.format(title.replace(' ', '-'))
            result['torrentfile'] = core.providers.torrent.magnet(i['hash'])
            result['guid'] = i['hash']
            result['type'] = 'magnet'
            result['downloadid'] = None
            result['freeleech'] = 0
            result['download_client'] = None
            result['seeders'] = i['seeds']

            results.append(result)
        except Exception as e:
            logging.error('Error parsing YTS JSON.', exc_info=True)
            continue

    logging.info('Found {} results from YTS'.format(len(results)))
    return results


def _parse_rss(xml):
    '''
    Since xml doesn't supply seeds I hard-coded in 5. Not ideal, but it is
        probably safe to assume that new YTS releases will have 5 seeds.
    '''
    logging.info('Parsing YTS RSS.')

    tree = ET.fromstring(xml)

    items = tree[0].findall('item')

    results = []
    for i in items:
        result = {}
        try:
            human_size = i[1].text.split('Size: ')[1].split('<')[0]
            m = (1024 ** 2) if human_size[2] == 'MB' else (1024 ** 3)

            title = i[0].text.split(' [')[0]
            quality = i[3].text.split('#')[-1]

            result['score'] = 0
            result['size'] = int(float(human_size.split(' ')[0]) * m)
            result['status'] = 'Available'
            result['pubdate'] = None
            result['title'] = '{}.Bluray.{}.YTS'.format(title, quality)
            result['imdbid'] = None
            result['indexer'] = 'YTS'
            result['info_link'] = i.find('link').text
            result['guid'] = i.find('enclosure').attrib['url'].split('/')[-1]
            result['torrentfile'] = core.providers.torrent.magnet(result['guid'])
            result['type'] = 'magnet'
            result['downloadid'] = None
            result['seeders'] = 5
            result['download_client'] = None
            result['freeleech'] = 0

            results.append(result)
        except Exception as e:
            logging.error('Error parsing YTS XML.', exc_info=True)
            continue

    logging.info('Found {} results from YTS'.format(len(results)))
    return results

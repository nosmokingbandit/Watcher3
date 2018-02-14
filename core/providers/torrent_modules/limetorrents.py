import core
from xml.etree.cElementTree import fromstring
from xmljson import yahoo
import logging
from core.helpers import Url

logging = logging.getLogger(__name__)


def search(imdbid, term):
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Performing backlog search on LimeTorrents for {}.'.format(imdbid))

    url = 'https://www.limetorrents.cc/searchrss/{}'.format(term)

    try:
        if proxy_enabled and core.proxy.whitelist('https://www.limetorrents.cc') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            return _parse(response, imdbid)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('LimeTorrent search failed.', exc_info=True)
        return []


def get_rss():
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Fetching latest RSS from ')

    url = 'https://www.limetorrents.cc/rss/16/'

    try:
        if proxy_enabled and core.proxy.whitelist('https://www.limetorrents.cc') is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            return _parse(response, None)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('LimeTorrent RSS fetch failed.', exc_info=True)
        return []


def _parse(xml, imdbid):
    logging.info('Parsing LimeTorrents results.')

    try:
        items = yahoo.data(fromstring(xml))['rss']['channel']['item']
    except Exception as e:
        logging.error('Unexpected XML format from ', exc_info=True)
        return []

    results = []
    for i in items:
        result = {}
        try:
            result['score'] = 0
            result['size'] = int(i['size'])
            result['status'] = 'Available'
            result['pubdate'] = None
            result['title'] = i['title']
            result['imdbid'] = imdbid
            result['indexer'] = 'LimeTorrents'
            result['info_link'] = i['link']
            result['torrentfile'] = i['enclosure']['url']
            result['guid'] = result['torrentfile'].split('.')[1].split('/')[-1].lower()
            result['type'] = 'torrent'
            result['downloadid'] = None
            result['freeleech'] = 0
            result['download_client'] = None

            s = i['description'].split('Seeds: ')[1]
            seed_str = ''
            while s[0].isdigit():
                seed_str += s[0]
                s = s[1:]

            result['seeders'] = int(seed_str)

            results.append(result)
        except Exception as e:
            logging.error('Error parsing LimeTorrents XML.', exc_info=True)
            continue

    logging.info('Found {} results from Limetorrents.'.format(len(results)))
    return results

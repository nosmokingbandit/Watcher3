import logging
import datetime
import xml.etree.cElementTree as ET
import core
from core.helpers import Url

logging = logging.getLogger(__name__)

'''
Does not supply rss feed -- backlog searches only.
'''


def search(imdbid, term):
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Searching Zooqle for {}.'.format(term))

    url = 'https://zooqle.com/search?q={}&fmt=rss'.format(term)

    try:
        if proxy_enabled and core.proxy.whitelist('https://www.zooqle.com') is True:
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
        logging.error('Zooqle search failed.', exc_info=True)
        return []


def get_rss():
    return []


def _parse(xml, imdbid):
    logging.info('Parsing Zooqle results.')

    tree = ET.fromstring(xml)

    items = tree[0].findall('item')

    results = []
    for i in items:
        result = {}
        try:
            result['score'] = 0

            size, suffix = i.find('description').text.strip().split(', ')[-1].split(' ')
            m = (1024 ** 2) if suffix == 'MB' else (1024 ** 3)
            result['size'] = int(float(size.replace(',', '')) * m)

            result['status'] = 'Available'

            pd = i.find('pubDate').text
            result['pubdate'] = datetime.datetime.strftime(datetime.datetime.strptime(pd, '%a, %d %b %Y %H:%M:%S %z'), '%d %b %Y')

            result['title'] = i.find('title').text
            result['imdbid'] = imdbid
            result['indexer'] = 'Zooqle'
            result['info_link'] = i.find('guid').text
            result['torrentfile'] = i[8].text
            result['guid'] = i[7].text.lower()
            result['type'] = 'magnet'
            result['downloadid'] = None
            result['freeleech'] = 0
            result['download_client'] = None
            result['seeders'] = int(i[9].text)

            results.append(result)
        except Exception as e:
            logging.error('Error parsing Zooqle XML.', exc_info=True)
            continue

    logging.info('Found {} results from Zooqle.'.format(len(results)))
    return results

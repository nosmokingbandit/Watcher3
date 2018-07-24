import logging
import xml.etree.cElementTree as ET
import core
from core.helpers import Url


def search(imdbid, term):
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Performing backlog search on ThePirateBay for {}.'.format(imdbid))

    url = 'https://www.thepiratebay.org/search/{}/0/99/200'.format(imdbid)

    headers = {'Cookie': 'lw=s'}
    try:
        if proxy_enabled and core.proxy.whitelist('https://www.thepiratebay.org') is True:
            response = Url.open(url, proxy_bypass=True, headers=headers).text
        else:
            response = Url.open(url, headers=headers).text

        if response:
            return _parse(response, imdbid)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('ThePirateBay search failed.', exc_info=True)
        return []


def get_rss():
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Fetching latest RSS from ThePirateBay.')

    url = 'https://www.thepiratebay.org/browse/201/0/3/0'
    headers = {'Cookie': 'lw=s'}
    try:
        if proxy_enabled and core.proxy.whitelist('https://www.thepiratebay.org') is True:
            response = Url.open(url, proxy_bypass=True, headers=headers).text
        else:
            response = Url.open(url, headers=headers).text

        if response:
            return _parse(response, None)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('ThePirateBay RSS fetch failed.', exc_info=True)
        return []


def _parse(html, imdbid):
    logging.info('Parsing ThePirateBay results.')

    html = ' '.join(html.split())
    rows = []
    for i in html.split('<tr>')[1:-1]:
        rows = rows + i.split('<tr class="alt">')

    rows = ['<tr>{}'.format(i.replace('&', '%26')) for i in rows]

    results = []
    for row in rows:
        i = ET.fromstring(row)
        result = {}
        try:

            result['title'] = i[1][0].text or i[1][0].attrib.get('title')
            if not result['title']:
                continue

            desc = i[4].text
            m = (1024 ** 3) if desc.split(';')[-1] == 'GiB' else (1024 ** 2)

            size = float(desc.split('%')[0]) * m

            result['score'] = 0
            result['size'] = size
            result['status'] = 'Available'
            result['pubdate'] = None
            result['imdbid'] = imdbid
            result['indexer'] = 'ThePirateBay'
            result['info_link'] = 'https://www.thepiratebay.org{}'.format(i[1][0].attrib['href'])
            result['torrentfile'] = i[3][0][0].attrib['href'].replace('%26', '&')
            result['guid'] = result['torrentfile'].split('&')[0].split(':')[-1]
            result['type'] = 'magnet'
            result['downloadid'] = None
            result['download_client'] = None
            result['seeders'] = int(i[5].text)
            result['freeleech'] = 0

            results.append(result)
        except Exception as e:
            logging.error('Error parsing ThePirateBay XML.', exc_info=True)
            continue

    logging.info('Found {} results from ThePirateBay.'.format(len(results)))
    return results

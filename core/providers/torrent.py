import json
import logging
import datetime
import time
import xml.etree.cElementTree as ET
import core
from core import sqldb
from core.proxy import Proxy
from core.helpers import Url
from core.providers.base import NewzNabProvider


logging = logging.getLogger(__name__)


class Torrent(NewzNabProvider):

    trackers = ['udp://tracker.leechers-paradise.org:6969',
                'udp://zer0day.ch:1337',
                'udp://tracker.coppersurfer.tk:6969',
                'udp://public.popcorn-tracker.org:6969'
                ]

    def __init__(self):
        self.feed_type = 'torrent'
        self.sql = sqldb.SQL()
        return

    def search_all(self, imdbid, title, year):
        ''' Search all Torrent indexers.
        imdbid: string imdb movie id.
        title: str movie title
        year: str year of movie release

        Returns list of dicts with sorted nzb information.
        '''

        torz_indexers = core.CONFIG['Indexers']['TorzNab'].values()

        self.imdbid = imdbid

        results = []

        term = Url.encode('{}+{}'.format(title, year))

        for indexer in torz_indexers:
            if indexer[2] is False:
                continue
            url_base = indexer[0]
            if url_base[-1] != '/':
                url_base = url_base + '/'
            apikey = indexer[1]

            caps = self.sql.torznab_caps(url_base)
            if not caps:
                caps = self._get_caps(url_base)
                if caps is None:
                    logging.error('Unable to get caps for {}'.format(url_base))
                    continue

            if 'imdbid' in caps:
                logging.info('{} supports imdbid search.'.format(url_base))
                r = self.search_newznab(url_base, apikey, t='movie', cat=2000, imdbid=imdbid)
            else:
                logging.info('{} does not support imdbid search, using q={}'.format(url_base, term))
                r = self.search_newznab(url_base, apikey, t='search', cat=2000, q=term)
            for i in r:
                results.append(i)

        torrent_indexers = core.CONFIG['Indexers']['Torrent']

        title = Url.encode(title)
        year = Url.encode(year)

        if torrent_indexers['rarbg']:
            rarbg_results = Rarbg.search(imdbid)
            for i in rarbg_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['limetorrents']:
            lime_results = LimeTorrents.search(imdbid, term)
            for i in lime_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['extratorrent']:
            extra_results = ExtraTorrent.search(imdbid, term)
            for i in extra_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['skytorrents']:
            sky_results = SkyTorrents.search(imdbid, term)
            for i in sky_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['torrentz2']:
            torrentz_results = Torrentz2.search(imdbid, term)
            for i in torrentz_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['thepiratebay']:
            tpb_results = ThePirateBay.search(imdbid)
            for i in tpb_results:
                if i not in results:
                    results.append(i)

        self.imdbid = None
        return results

    def get_rss(self):
        ''' Gets rss from all torznab providers and individual providers

        Returns list of dicts of latest movies
        '''

        results = []

        results = self._get_rss()

        torrent_indexers = core.CONFIG['Indexers']['Torrent']

        if torrent_indexers['rarbg']:
            rarbg_results = Rarbg.get_rss()
            for i in rarbg_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['limetorrents']:
            lime_results = LimeTorrents.get_rss()
            for i in lime_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['extratorrent']:
            extra_results = ExtraTorrent.get_rss()
            for i in extra_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['torrentz2']:
            torrentz_results = Torrentz2.get_rss()
            for i in torrentz_results:
                if i not in results:
                    results.append(i)

        return results

    def _get_caps(self, url):
        ''' Gets caps for indexer url
        url: string url of torznab indexer

        Stores caps in CAPS table

        Returns list of caps
        '''
        caps_url = '{}?t=caps'.format(url)

        request = Url.request(caps_url)

        xml = Url.open(request)['body']
        root = ET.fromstring(xml)
        caps = root[0].find('movie-search').attrib['supportedParams']

        self.sql.write('CAPS', {'url': url, 'caps': caps})

        return caps.split(',')


class Rarbg(object):
    '''
    This api is limited to once request every 2 seconds.
    '''

    timeout = None
    token = None

    @staticmethod
    def search(imdbid):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching Rarbg for {}.'.format(imdbid))
        if Rarbg.timeout:
            now = datetime.datetime.now()
            while Rarbg.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        if not Rarbg.token:
            Rarbg.token = Rarbg.get_token()
            if Rarbg.token is None:
                logging.error('Unable to get Rarbg token.')
                return []

        url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=search&search_imdb={}&category=movies&format=json_extended&app_id=Watcher'.format(Rarbg.token, imdbid)

        request = Url.request(url)

        Rarbg.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.torrentapi.org') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            results = json.loads(response).get('torrent_results')
            if results:
                return Rarbg.parse(results)
            else:
                logging.info('Nothing found on Rarbg.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Rarbg search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Rarbg.')
        if Rarbg.timeout:
            now = datetime.datetime.now()
            while Rarbg.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        if not Rarbg.token:
            Rarbg.token = Rarbg.get_token()
            if Rarbg.token is None:
                logging.error('Unable to get Rarbg token.')
                return []

        url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=list&category=movies&format=json_extended&app_id=Watcher'.format(Rarbg.token)

        request = Url.request(url)

        Rarbg.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.torrentapi.org') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            results = json.loads(response).get('torrent_results')
            if results:
                return Rarbg.parse(results)
            else:
                logging.info('Nothing found in Rarbg RSS.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Rarbg RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def get_token():
        url = 'https://www.torrentapi.org/pubapi_v2.php?get_token=get_token'

        request = Url.request(url)

        try:
            result = json.loads(Url.open(request)['body'])
            token = result.get('token')
            return token
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Failed to get Rarbg token.', exc_info=True)
            return None

    @staticmethod
    def parse(results):
        logging.info('Parsing Rarbg results.')
        item_keep = ('size', 'pubdate', 'title', 'indexer', 'info_link', 'guid', 'torrentfile', 'resolution', 'type', 'seeders')

        parsed_results = []

        for result in results:
            result['indexer'] = 'www.rarbg.to'
            result['info_link'] = result['info_page']
            result['torrentfile'] = result['download']
            result['guid'] = result['download'].split('&')[0].split(':')[-1]
            result['type'] = 'magnet'
            result['pubdate'] = None

            result = {k: v for k, v in result.items() if k in item_keep}

            result['status'] = 'Available'
            result['score'] = 0
            result['downloadid'] = None
            result['freeleech'] = 0
            parsed_results.append(result)
        logging.info('Found {} results from Rarbg.'.format(len(parsed_results)))
        return parsed_results


class LimeTorrents(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching LimeTorrents for {}.'.format(term))

        url = 'https://www.limetorrents.cc/searchrss/{}'.format(term)
        request = Url.request(url)

        try:
            if proxy_enabled and Proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return LimeTorrents.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('LimeTorrent search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from LimeTorrents.')

        url = 'https://www.limetorrents.cc/rss/16/'
        request = Url.request(url)

        try:
            if proxy_enabled and Proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return LimeTorrents.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('LimeTorrent RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing LimeTorrents results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0
                result['size'] = int(i.find('size').text)
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i.find('title').text
                result['imdbid'] = imdbid
                result['indexer'] = 'www.limetorrents.cc'
                result['info_link'] = i.find('comments').text
                result['torrentfile'] = i.find('enclosure').attrib['url']
                result['guid'] = result['torrentfile'].split('.')[1].split('/')[-1].lower()
                result['type'] = 'torrent'
                result['downloadid'] = None
                result['freeleech'] = 0

                s = i.find('description').text.split('Seeds: ')[1]
                seed_str = ''
                while s[0].isdigit():
                    seed_str += s[0]
                    s = s[1:]

                result['seeders'] = int(seed_str)

                results.append(result)
            except Exception as e:
                logging.error('Error parsing LimeTorrents XML.', exc_info=True)
                continue

        logging.info('Found {} results from LimeTorrents.'.format(len(results)))
        return results


class ExtraTorrent(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching ExtraTorrent for {}.'.format(term))

        url = 'https://www.extratorrent.cc/rss.xml?type=search&cid=4&search={}'.format(term)

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.extratorrent.cc') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return ExtraTorrent.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('ExtraTorrent search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from ExtraTorrent.')

        url = 'https://www.extratorrent.cc/rss.xml?cid=4&type=today'

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.extratorrent.cc') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return ExtraTorrent.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('ExtraTorrent RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing ExtraTorrent results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0
                result['size'] = int(i.find('size').text)
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i.find('title').text
                result['imdbid'] = imdbid
                result['indexer'] = 'www.extratorrent.cc'
                result['info_link'] = i.find('link').text
                result['torrentfile'] = i.find('magnetURI').text
                result['guid'] = result['torrentfile'].split('&')[0].split(':')[-1]
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['freeleech'] = 0

                seeders = i.find('seeders').text
                result['seeders'] = 0 if seeders == '---' else seeders

                results.append(result)
            except Exception as e:
                logging.error('Error parsing ExtraTorrent XML.', exc_info=True)
                continue

        logging.info('Found {} results from ExtraTorrent.'.format(len(results)))
        return results


class SkyTorrents(object):
    ''' Does not supply rss feed -- backlog searches only. '''

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching SkyTorrents for {}.'.format(term))

        url = 'https://www.skytorrents.in/rss/all/ed/1/{}'.format(term)

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.skytorrents.in') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return SkyTorrents.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('SkyTorrents search failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing SkyTorrents results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0

                desc = i.find('description').text.split(' ')

                m = (1024 ** 2) if desc[-2] == 'MB' else (1024 ** 3)
                result['size'] = int(float(desc[-3]) * m)

                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i.find('title').text
                result['imdbid'] = imdbid
                result['indexer'] = 'www.skytorrents.in'
                result['info_link'] = i.find('guid').text
                result['torrentfile'] = i.find('link').text
                result['guid'] = result['torrentfile'].split('/')[4]
                result['type'] = 'torrent'
                result['downloadid'] = None
                result['freeleech'] = 0

                result['seeders'] = desc[0]

                results.append(result)
            except Exception as e: #noqa
                logging.error('Error parsing SkyTorrents XML.', exc_info=True)
                continue

        logging.info('Found {} results from SkyTorrents.'.format(len(results)))
        return results


class Torrentz2(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching Torrentz2 for {}.'.format(term))

        url = 'https://www.torrentz2.eu/feed?f={}'.format(term)

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.torrentz2.e') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return Torrentz2.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Torrentz2 search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Torrentz2.')

        url = 'https://www.torrentz2.eu/feed?f=movies'

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.torrentz2.e') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return Torrentz2.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Torrentz2 RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing Torrentz2 results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                desc = i.find('description').text.split(' ')
                hsh = desc[-1]

                m = (1024 ** 2) if desc[2] == 'MB' else (1024 ** 3)

                result['score'] = 0
                result['size'] = int(desc[1]) * m
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i.find('title').text
                result['imdbid'] = imdbid
                result['indexer'] = 'www.torrentz2.e'
                result['info_link'] = i.find('link').text
                result['torrentfile'] = 'magnet:?xt=urn:btih:{}&dn={}&tr={}'.format(hsh, result['title'], '&tr='.join(Torrent.trackers))
                result['guid'] = hsh
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['seeders'] = int(desc[4])
                result['freeleech'] = 0

                results.append(result)
            except Exception as e:
                logging.error('Error parsing Torrentz2 XML.', exc_info=True)
                continue

        logging.info('Found {} results from Torrentz2.'.format(len(results)))
        return results


class ThePirateBay(object):

    @staticmethod
    def search(imdbid):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching ThePirateBay for {}.'.format(imdbid))

        url = 'https://www.thepiratebay.org/search/{}/0/99/200'.format(imdbid)

        request = Url.request(url)
        request.add_header('Cookie', 'lw=s')
        try:
            if proxy_enabled and Proxy.whitelist('https://www.thepiratebay.org') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return ThePirateBay.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('ThePirateBay search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from ThePirateBay.')

        url = 'https://www.thepiratebay.org/browse/201/0/3/0'

        request = Url.request(url)
        try:
            if proxy_enabled and Proxy.whitelist('https://www.thepiratebay.org') is True:
                response = Proxy.bypass(request)['body']
            else:
                response = Url.open(request)['body']

            if response:
                return ThePirateBay.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('ThePirateBay RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(html, imdbid):
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

                desc = i[4].text
                m = (1024 ** 3) if desc.split(';')[-1] == 'GiB' else (1024 ** 2)

                size = float(desc.split('%')[0]) * m

                result['score'] = 0
                result['size'] = size
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i[1][0].text
                result['imdbid'] = imdbid
                result['indexer'] = 'www.thepiratebay.org'
                result['info_link'] = 'https://www.thepiratebay.org{}'.format(i[1][0].attrib['href'])
                result['torrentfile'] = i[3][0][0].attrib['href'].replace('%26', '&')
                result['guid'] = result['torrentfile'].split('&')[0].split(':')[-1]
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['seeders'] = int(i[5].text)
                result['freeleech'] = 0

                results.append(result)
            except Exception as e:
                logging.error('Error parsing ThePirateBay XML.', exc_info=True)
                continue

        logging.info('Found {} results from ThePirateBay.'.format(len(results)))
        return results

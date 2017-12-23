import json
import logging
import datetime
import time
import xml.etree.cElementTree as ET
from xml.etree.cElementTree import fromstring
from xmljson import yahoo
import core
from core import proxy
from core.helpers import Url
from core.providers.base import NewzNabProvider


logging = logging.getLogger(__name__)


trackers = '&tr'.join(('udp://tracker.leechers-paradise.org:6969',
                       'udp://zer0day.ch:1337',
                       'udp://tracker.coppersurfer.tk:6969',
                       'udp://public.popcorn-tracker.org:6969',
                       'udp://open.demonii.com:1337/announce',
                       'udp://tracker.openbittorrent.com:80',
                       'udp://tracker.coppersurfer.tk:6969',
                       'udp://glotorrents.pw:6969/announce',
                       'udp://tracker.opentrackr.org:1337/announce',
                       'udp://torrent.gresille.org:80/announce',
                       'udp://p4p.arenabg.com:1337',
                       'udp://tracker.leechers-paradise.org:6969'
                       ))


def magnet(hash_):
    ''' Creates magnet link
    hash_ (str): base64 formatted torrent hash

    Formats as magnet uri and adds trackers

    Returns str margnet uri
    '''

    return 'magnet:?xt=urn:btih:{}&tr={}'.format(hash_, trackers)


class Torrent(NewzNabProvider):

    def __init__(self):
        self.feed_type = 'torrent'
        return

    def search_all(self, imdbid, title, year):
        ''' Performs backlog search for all indexers.
        imdbid (str): imdb id #
        title (str): movie title
        year (str/int): year of movie release

        Returns list of dicts with sorted release information.
        '''

        torz_indexers = core.CONFIG['Indexers']['TorzNab'].values()

        self.imdbid = imdbid

        results = []

        term = Url.normalize('{} {}'.format(title, year))

        for indexer in torz_indexers:
            if indexer[2] is False:
                continue
            url_base = indexer[0]
            logging.info('Searching TorzNab indexer {}'.format(url_base))
            if url_base[-1] != '/':
                url_base = url_base + '/'
            apikey = indexer[1]

            caps = core.sql.torznab_caps(url_base)
            if not caps:
                caps = self._get_caps(url_base, apikey)
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

        title = Url.normalize(title)
        year = Url.normalize(str(year))

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
        if torrent_indexers['torrentdownloads']:
            tordls = TorrentDownloads.search(imdbid, term)
            for i in tordls:
                if i not in results:
                    results.append(i)
        if torrent_indexers['yts']:
            yts_results = YTS.search(imdbid, term)
            for i in yts_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['zooqle']:
            zooqle_results = Zooqle.search(imdbid, term)
            for i in zooqle_results:
                if i not in results:
                    results.append(i)

        self.imdbid = None
        return results

    def get_rss(self):
        ''' Gets rss from all torznab providers and individual providers

        Returns list of dicts of latest movies
        '''

        logging.info('Syncing Torrent indexer RSS feeds.')

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
        if torrent_indexers['thepiratebay']:
            thepiratebay_results = ThePirateBay.get_rss()
            for i in thepiratebay_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['torrentdownloads']:
            tordls = TorrentDownloads.get_rss()
            for i in tordls:
                if i not in results:
                    results.append(i)
        if torrent_indexers['torrentz2']:
            torrentz_results = Torrentz2.get_rss()
            for i in torrentz_results:
                if i not in results:
                    results.append(i)
        if torrent_indexers['yts']:
            yts_results = YTS.get_rss()
            for i in yts_results:
                if i not in results:
                    results.append(i)
        return results

    def _get_caps(self, url_base, apikey):
        ''' Gets caps for indexer url
        url_base (str): url of torznab indexer
        apikey (str): api key for indexer

        Gets indexer caps from CAPS table

        Returns list of caps
        '''

        logging.info('Getting caps for {}'.format(url_base))

        url = '{}api?apikey={}&t=caps'.format(url_base, apikey)

        try:
            xml = Url.open(url).text

            caps = yahoo.data(fromstring(xml))['caps']['searching']['movie-search']['supportedParams']

            core.sql.write('CAPS', {'url': url_base, 'caps': caps})
        except Exception as e:
            logging.warning('', exc_info=True)
            return None

        return caps.split(',')


class RarbgTokenError(Exception):
    ''' Raised when a Rarbg token cannot be retrieved '''
    def __init__(self, msg=None):
        self.msg = msg if msg else 'Failed to retrieve new token from Rarbg\'s torrentapi.org.'


class Rarbg(object):
    '''
    This api is limited to one request every 2 seconds.
    '''

    timeout = None
    _token = None
    _token_timeout = datetime.datetime.now()

    @staticmethod
    def token():
        ''' Gets/sets token and monitors token timeout

        Returns str rarbg token
        '''
        if not Rarbg._token:
            Rarbg._token = Rarbg._get_token()
        else:
            now = datetime.datetime.now()
            if (now - Rarbg._token_timeout).total_seconds() > 900:
                Rarbg._token = Rarbg._get_token()
                Rarbg._token_timeout = now
        return Rarbg._token

    @staticmethod
    def search(imdbid):
        ''' Search api for movie
        imdbid (str): imdb id #

        Returns list of dicts of parsed releases
        '''

        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on Rarbg for {}.'.format(imdbid))
        if Rarbg.timeout:
            now = datetime.datetime.now()
            while Rarbg.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        try:
            url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=search&search_imdb={}&category=movies&format=json_extended&app_id=Watcher'.format(Rarbg.token(), imdbid)

            Rarbg.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

            if proxy_enabled and proxy.whitelist('https://www.torrentapi.org') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            results = json.loads(response).get('torrent_results')
            if results:
                return Rarbg.parse(results, imdbid=imdbid)
            else:
                logging.info('Nothing found on Rarbg.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Rarbg search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        ''' Gets latest rss feed from api

        Returns list of dicts of parsed releases
        '''
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Rarbg.')
        if Rarbg.timeout:
            now = datetime.datetime.now()
            while Rarbg.timeout > now:
                time.sleep(1)
                now = datetime.datetime.now()

        try:
            url = 'https://www.torrentapi.org/pubapi_v2.php?token={}&mode=list&category=movies&format=json_extended&app_id=Watcher'.format(Rarbg.token())
            Rarbg.timeout = datetime.datetime.now() + datetime.timedelta(seconds=2)

            if proxy_enabled and proxy.whitelist('https://www.torrentapi.org') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            results = json.loads(response).get('torrent_results')
            if results:
                return Rarbg.parse(results)
            else:
                logging.info('Nothing found in Rarbg RSS.')
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Rarbg RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def _get_token():
        ''' Get api access token

        Returns str or None
        '''
        logging.info('Getting RarBG access token.')
        url = 'https://www.torrentapi.org/pubapi_v2.php?get_token=get_token'

        try:
            result = json.loads(Url.open(url).text)
            token = result.get('token')
            return token
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Failed to get Rarbg token.', exc_info=True)
            raise RarbgTokenError(str(e))

    @staticmethod
    def parse(results, imdbid=None):
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
        logging.info('Found {} results from Rarbg.'.format(len(parsed_results)))
        return parsed_results


class LimeTorrents(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on LimeTorrents for {}.'.format(imdbid))

        url = 'https://www.limetorrents.cc/searchrss/{}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return LimeTorrents.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('LimeTorrent search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from LimeTorrents.')

        url = 'https://www.limetorrents.cc/rss/16/'

        try:
            if proxy_enabled and proxy.whitelist('https://www.limetorrents.cc') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return LimeTorrents.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('LimeTorrent RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing LimeTorrents results.')

        try:
            items = yahoo.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from LimeTorrents.', exc_info=True)
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

        logging.info('Found {} results from LimeTorrents.'.format(len(results)))
        return results


class YTS(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on YTS for {}.'.format(imdbid))

        url = 'https://yts.ag/api/v2/list_movies.json?limit=1&query_term={}'.format(imdbid)

        try:
            if proxy_enabled and proxy.whitelist('https://www.yts.ag') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                r = json.loads(response)
                if r['data']['movie_count'] < 1:
                    return []
                else:
                    return YTS.parse(r['data']['movies'][0], imdbid, term)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('YTS search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from YTS.')

        url = 'https://yts.ag/rss/0/all/all/0'

        try:
            if proxy_enabled and proxy.whitelist('https://www.yts.ag') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return YTS.parse_rss(response)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('YTS RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(movie, imdbid, title):
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
                result['info_link'] = 'https://yts.ag/movie/{}'.format(title.replace(' ', '-'))
                result['torrentfile'] = magnet(i['hash'])
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

        logging.info('Found {} results from YTS.'.format(len(results)))
        return results

    @staticmethod
    def parse_rss(xml):
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
                result['torrentfile'] = magnet(result['guid'])
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['seeders'] = 5
                result['download_client'] = None
                result['freeleech'] = 0

                results.append(result)
            except Exception as e:
                logging.error('Error parsing YTS XML.', exc_info=True)
                continue

        logging.info('Found {} results from YTS.'.format(len(results)))
        return results


class SkyTorrents(object):
    ''' Does not supply rss feed -- backlog searches only. '''

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on SkyTorrents for {}.'.format(imdbid))

        url = 'https://www.skytorrents.in/rss/all/ed/1/{}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.skytorrents.in') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return SkyTorrents.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
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
                result['indexer'] = 'SkyTorrents'
                result['info_link'] = i.find('guid').text
                result['torrentfile'] = i.find('link').text
                result['guid'] = result['torrentfile'].split('/')[4]
                result['type'] = 'torrent'
                result['download_client'] = None
                result['downloadid'] = None
                result['freeleech'] = 0

                result['seeders'] = desc[0]

                results.append(result)
            except Exception as e:
                logging.error('Error parsing SkyTorrents XML.', exc_info=True)
                continue

        logging.info('Found {} results from SkyTorrents.'.format(len(results)))
        return results


class Torrentz2(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on Torrentz2 for {}.'.format(imdbid))

        url = 'https://www.torrentz2.eu/feed?f={}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.torrentz2.e') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return Torrentz2.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Torrentz2 search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from Torrentz2.')

        url = 'https://www.torrentz2.eu/feed?f=movies'

        try:
            if proxy_enabled and proxy.whitelist('https://www.torrentz2.e') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return Torrentz2.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Torrentz2 RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing Torrentz2 results.')

        try:
            items = yahoo.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from Torrentz2.', exc_info=True)
            return []

        results = []
        for i in items:
            result = {}
            try:
                desc = i['description'].split(' ')
                hash_ = desc[-1]

                m = (1024 ** 2) if desc[2] == 'MB' else (1024 ** 3)

                result['score'] = 0
                result['size'] = int(desc[1]) * m
                result['status'] = 'Available'
                result['pubdate'] = None
                result['title'] = i['title']
                result['imdbid'] = imdbid
                result['indexer'] = 'Torrentz2'
                result['info_link'] = i['link']
                result['torrentfile'] = magnet(hash_)
                result['guid'] = hash_
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['seeders'] = int(desc[4])
                result['download_client'] = None
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

        logging.info('Performing backlog search on ThePirateBay for {}.'.format(imdbid))

        url = 'https://www.thepiratebay.org/search/{}/0/99/200'.format(imdbid)

        headers = {'Cookie': 'lw=s'}
        try:
            if proxy_enabled and proxy.whitelist('https://www.thepiratebay.org') is True:
                response = Url.open(url, proxy_bypass=True, headers=headers).text
            else:
                response = Url.open(url, headers=headers).text

            if response:
                return ThePirateBay.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('ThePirateBay search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from ThePirateBay.')

        url = 'https://www.thepiratebay.org/browse/201/0/3/0'
        headers = {'Cookie': 'lw=s'}
        try:
            if proxy_enabled and proxy.whitelist('https://www.thepiratebay.org') is True:
                response = Url.open(url, proxy_bypass=True, headers=headers).text
            else:
                response = Url.open(url, headers=headers).text

            if response:
                return ThePirateBay.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
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


class Zooqle(object):
    ''' Does not supply rss feed -- backlog searches only. '''

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Searching Zooqle for {}.'.format(term))

        url = 'https://zooqle.com/search?q={}&fmt=rss'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('https://www.zooqle.com') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return Zooqle.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Zooqle search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        # This does nothing. Does Zooqle have a new releases feed?
        return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing Zooqle results.')

        tree = ET.fromstring(xml)

        items = tree[0].findall('item')

        results = []
        for i in items:
            result = {}
            try:
                result['score'] = 0

                size, suffix = i.find('description').text.strip().split(', ')[1].split(' ')
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


class TorrentDownloads(object):

    @staticmethod
    def search(imdbid, term):
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Performing backlog search on TorrentDownloads for {}.'.format(imdbid))

        url = 'http://www.torrentdownloads.me/rss.xml?type=search&search={}'.format(term)

        try:
            if proxy_enabled and proxy.whitelist('http://www.torrentdownloads.me') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return TorrentDownloads.parse(response, imdbid)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('TorrentDownloads search failed.', exc_info=True)
            return []

    @staticmethod
    def get_rss():
        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        logging.info('Fetching latest RSS from TorrentDownloads.')

        url = 'http://www.torrentdownloads.me/rss2/last/4'

        try:
            if proxy_enabled and proxy.whitelist('http://www.torrentdownloads.me') is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            if response:
                return TorrentDownloads.parse(response, None)
            else:
                return []
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('TorrentDownloads RSS fetch failed.', exc_info=True)
            return []

    @staticmethod
    def parse(xml, imdbid):
        logging.info('Parsing TorrentDownloads results.')

        try:
            items = yahoo.data(fromstring(xml))['rss']['channel']['item']
        except Exception as e:
            logging.error('Unexpected XML format from TorrentDownloads.', exc_info=True)
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
                result['indexer'] = 'TorrentDownloads'
                result['info_link'] = 'http://www.torrentdownloads.me{}'.format(i['link'])
                result['torrentfile'] = magnet(i['info_hash'])
                result['guid'] = i['info_hash']
                result['type'] = 'magnet'
                result['downloadid'] = None
                result['freeleech'] = 0
                result['download_client'] = None
                result['seeders'] = int(i['seeders'])

                results.append(result)
            except Exception as e:
                logging.error('Error parsing TorrentDownloads XML.', exc_info=True)
                continue

        logging.info('Found {} results from TorrentDownloads.'.format(len(results)))
        return results

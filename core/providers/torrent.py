from xml.etree.cElementTree import fromstring
from xmljson import yahoo
import core
from core.helpers import Url
from core.providers.base import NewzNabProvider
from core.providers import torrent_modules  # noqa
import logging

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
                r = self.search_newznab(url_base, apikey, 'movie', imdbid=imdbid)
            else:
                logging.info('{} does not support imdbid search, using q={}'.format(url_base, term))
                r = self.search_newznab(url_base, apikey, 'search', q=term, imdbid=imdbid)
            for i in r:
                results.append(i)

        for indexer, enabled in core.CONFIG['Indexers']['Torrent'].items():
            if enabled:
                if not hasattr(torrent_modules, indexer):
                    logging.warning('Torrent indexer {} enabled but not found in torrent_modules.'.format(indexer))
                    continue
                else:
                    for i in getattr(torrent_modules, indexer).search(imdbid, term):
                        if i not in results:
                            results.append(i)

        for indexer, indexerobject in core.CONFIG['Indexers']['PrivateTorrent'].items():
            if indexerobject['enabled']:
                if not hasattr(torrent_modules, indexer):
                    logging.warning('Torrent indexer {} enabled but not found in torrent_modules.'.format(indexer))
                    continue
                else:
                    for i in getattr(torrent_modules, indexer).search(imdbid, term):
                        if i not in results:
                            results.append(i)

        return results

    def get_rss(self):
        ''' Gets rss from all torznab providers and individual providers

        Returns list of dicts of latest movies
        '''

        logging.info('Syncing Torrent indexer RSS feeds.')

        results = []

        results = self._get_rss()

        for indexer, enabled in core.CONFIG['Indexers']['Torrent'].items():
            if enabled:
                if not hasattr(torrent_modules, indexer):
                    logging.warning('Torrent indexer {} enabled but not found in torrent_modules.'.format(indexer))
                    continue
                else:
                    for i in getattr(torrent_modules, indexer).get_rss():
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

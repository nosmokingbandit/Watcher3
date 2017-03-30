import logging
import xml.etree.cElementTree as ET

from core import sqldb
from core.helpers import Url
from fuzzywuzzy import fuzz

logging = logging.getLogger(__name__)


class PreDB(object):

    def __init__(self):
        self.sql = sqldb.SQL()

    def check_all(self):
        ''' Checks all movies for predb status

        Simply loops through MOVIES table and executes self.check_one if
            predb column is not 'found'

        Returns bool False is movies cannot be retrieved
        '''

        logging.info('Checking predb.me for new available releases.')

        movies = self.sql.get_user_movies()
        if not movies:
            return False

        for movie in movies:
            if movie['predb'] != 'found':
                self.check_one(movie)

    def check_one(self, data):
        ''' Searches predb for releases and marks row in MOVIES
        :param data: dict data from row in MOVIES

        'data' requires key 'title', 'year', 'imdbid'

        Checks predb rss for releases. Marks row 'found' if found.

        Returns bool on success/failure
        '''

        title = data['title']
        year = data['year']
        title_year = '{} {}'.format(title, year)
        imdbid = data['imdbid']

        logging.info('Checking predb.me for new available releases for {}.'.format(title))

        rss_titles = self.search_rss(title_year)

        if not rss_titles:
            return False

        test = title_year.replace(' ', '.').lower()

        if self.fuzzy_match(rss_titles, test):
            logging.info('{} {} found on predb.me.'.format(title, year))
            if self.sql.update('MOVIES', 'predb', 'found', 'imdbid', imdbid):
                return True
            else:
                return False

    def search_rss(self, title_year):
        ''' Searches predb rss for title_year
        :param title_year: str movie title and year 'Black Swan 2010'

        Returns list of found rss entries or None if not found.
        '''

        title_year = Url.normalize(title_year)

        url = 'http://predb.me/?cats=movies&search={}&rss=1'.format(title_year)

        try:
            response = Url.open(url).text
            results_xml = response.replace('&', '%26')
            items = self.parse_predb_xml(results_xml)
            return items
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Predb.me search failed.', exc_info=True)
            return None

    def parse_predb_xml(self, feed):
        ''' Helper function to parse predb xmlrpclib
        :param feed: str rss feed

        Returns list of items with 'title' in tag
        '''

        root = ET.fromstring(feed)

        # This so ugly, but some newznab sites don't output json.
        items = []
        for item in root.iter('item'):
            for i_c in item:
                if i_c.tag == 'title':
                    items.append(i_c.text)
        return items

    # keeps checking release titles until one matches or all are checked
    def fuzzy_match(self, items, test):
        ''' Fuzzy matches title with predb rss titles
        :param items: list of titles in predb rss
        :param test: str to match to rss titles

        Returns bool if any one 'items' fuzzy matches above 50%
        '''

        for item in items:
            match = fuzz.partial_ratio(item, test)
            if match > 50:
                return True
        return False

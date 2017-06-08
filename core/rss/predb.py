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

        Simply loops through MOVIES table and executes self.backlog_search if
            predb column is not 'found'

        Returns bool False is movies cannot be retrieved
        '''

        logging.info('Checking predb.me for new available releases.')

        movies = self.sql.get_user_movies()
        if not movies:
            return False

        backlog_movies = [i for i in movies if i['predb_backlog'] != '1' and i['status'] != 'Disabled']
        rss_movies = [i for i in movies if i['predb_backlog'] == '1' and i['predb'] != 'found' and i['status'] != 'Disabled']

        if backlog_movies:
            logging.info('Performing predb backlog search for {}'.format(', '.join(i['title'] for i in backlog_movies)))
            for movie in backlog_movies:
                self.backlog_search(movie)

        if rss_movies:
            self._search_rss(rss_movies)

    def backlog_search(self, data):
        ''' Searches predb for releases and marks row in MOVIES
        :param data: dict data from row in MOVIES

        'data' requires key 'title', 'year', 'imdbid'

        Searches predb backlog for releases. Marks row predb:'found' and status:'Wanted'
            if found. Marks predb_backlog:1 as long as predb url request doesn't fail.

        Returns bool on success/failure
        '''

        title = data['title']
        year = data['year']
        title_year = '{} {}'.format(title, year)
        imdbid = data['imdbid']

        logging.info('Checking predb.me for new available releases for {}.'.format(title))

        predb_titles = self._search_db(title_year)

        if not predb_titles:
            return False

        test = title_year.replace(' ', '.').lower()
        db_update = {'predb': 'found', 'status': 'Wanted', 'predb_backlog': 1}

        if self._fuzzy_match(predb_titles, test):
            logging.info('{} {} found on predb.me.'.format(title, year))
            if self.sql.update_multiple('MOVIES', db_update, imdbid=imdbid):
                return True
            else:
                return False

    def _search_db(self, title_year):
        ''' Helper for backlog_search
        :param title_year: str movie title and year 'Black Swan 2010'

        Returns list of found predb entries or None if not found.
        '''

        title_year = Url.normalize(title_year)

        url = 'http://predb.me/?cats=movies&search={}&rss=1'.format(title_year)

        try:
            response = Url.open(url).text
            results_xml = response.replace('&', '%26')
            items = self._parse_predb_xml(results_xml)
            return items
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:  # noqa
            logging.error('Predb.me search failed.', exc_info=True)
            return None

    def _search_rss(self, movies):
        ''' Search rss feed for applicable releases
        movies: list of dicts of movies

        If found, marks movie in database as predb:'found' and status:'Wanted'

        Does not return
        '''
        db_update = {'predb': 'found', 'status': 'Wanted', 'predb_backlog': 1}

        logging.info('Checking predb rss for {}'.format(', '.join(i['title'] for i in movies)))

        try:
            feed = Url.open('https://predb.me/?cats=movies&rss=1').text
            items = self._parse_predb_xml(feed)

            for movie in movies:
                title = movie['title']
                year = movie['year']
                imdbid = movie['imdbid']

                test = '{}.{}'.format(title, year).replace(' ', '.')
                if self._fuzzy_match(items, test):
                    logging.info('{} {} found on predb.me RSS.'.format(title, year))
                    self.sql.update_multiple('MOVIES', db_update, imdbid=imdbid)
                    continue
        except Exception as e:
            logging.error('Unable to read predb rss.', exc_info=True)

    def _parse_predb_xml(self, feed):
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
    def _fuzzy_match(self, items, test):
        ''' Fuzzy matches title with predb titles
        :param items: list of titles in predb response
        :param test: str to match to rss titles

        Returns bool if any one 'items' fuzzy matches above 50%
        '''

        for item in items:
            match = fuzz.partial_ratio(item, test)
            if match > 50:
                return True
        return False

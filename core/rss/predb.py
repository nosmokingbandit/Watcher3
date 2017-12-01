import logging
import xml.etree.cElementTree as ET

import core
from core.helpers import Url
from stringscore import liquidmetal as lm

logging = logging.getLogger(__name__)


class PreDB(object):

    def check_all(self):
        ''' Checks all movies for predb status

        Simply loops through MOVIES table and executes self.backlog_search if
            predb column is not 'found'

        Returns bool
        '''

        logging.info('Checking predb.me for new available releases.')

        movies = core.sql.get_user_movies()
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

    def backlog_search(self, movie):
        ''' Searches predb for releases and marks row in MOVIES
        data (dict): data from row in MOVIES

        'data' requires key 'title', 'year', 'imdbid'

        Searches predb backlog for releases. Marks row predb:'found' and status:'Wanted'
            if found. Marks predb_backlog:1 as long as predb url request doesn't fail.

        Returns dict movie info after updating with predb results
        '''

        title = movie['title']
        year = str(movie['year'])
        title_year = '{} {}'.format(title, year)
        imdbid = movie['imdbid']

        logging.info('Checking predb.me for verified releases for {}.'.format(title))

        predb_titles = self._search_db(title_year)

        db_update = {'predb_backlog': 1}

        if predb_titles:
            if self._fuzzy_match(predb_titles, title, year):
                logging.info('{} {} found on predb.me.'.format(title, year))
                db_update['predb'] = 'found'

        movie.update(db_update)
        core.sql.update_multiple_values('MOVIES', db_update, imdbid=imdbid)

        return movie

    def _search_db(self, title_year):
        ''' Helper for backlog_search
        title_year (str): movie title and year 'Black Swan 2010'

        Returns list of found predb entries
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
        except Exception as e:
            logging.error('Predb.me search failed.', exc_info=True)
            return []

    def _search_rss(self, movies):
        ''' Search rss feed for applicable releases
        movies: list of dicts of movies

        If found, marks movie in database as predb:'found' and status:'Wanted'

        Does not return
        '''

        logging.info('Checking predb rss for {}'.format(', '.join(i['title'] for i in movies)))

        try:
            feed = Url.open('https://predb.me/?cats=movies&rss=1').text
            items = self._parse_predb_xml(feed)

            for movie in movies:
                title = movie['title']
                year = str(movie['year'])
                imdbid = movie['imdbid']

                if self._fuzzy_match(items, title, year):
                    logging.info('{} {} found on predb.me RSS.'.format(title, year))
                    core.sql.update('MOVIES', 'predb', 'found', 'imdbid', imdbid)
                    continue
        except Exception as e:
            logging.error('Unable to read predb rss.', exc_info=True)

    def _parse_predb_xml(self, feed):
        ''' Helper function to parse predb xmlrpclib
        feed (str): rss feed text

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
    def _fuzzy_match(self, predb_titles, title, year):
        ''' Fuzzy matches title with predb titles
        predb_titles (list): titles in predb response
        title (str): title to match to rss titles
        year (str): year of movie release

        Checks for any fuzzy match over 60%

        Returns bool
        '''

        movie = Url.normalize('{}.{}'.format(title, year)).replace(' ', '.')
        for pdb in predb_titles:
            if year not in pdb:
                continue
            pdb = pdb.split(year)[0] + year
            match = lm.score(pdb.replace(' ', '.'), movie) * 100
            if match > 60:
                logging.debug('{} matches {} at {}%'.format(pdb, movie, int(match)))
                return True
        return False

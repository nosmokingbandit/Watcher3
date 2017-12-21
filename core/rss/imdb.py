import core
from core import searcher
from core.movieinfo import TMDB
from core.helpers import Url
from datetime import datetime
import json
import logging
import os
import xml.etree.cElementTree as ET

logging = logging.getLogger(__name__)


class ImdbRss(object):
    def __init__(self):
        self.tmdb = TMDB()
        self.data_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'imdb')
        self.date_format = '%a, %d %b %Y %H:%M:%S %Z'
        self.searcher = searcher.Searcher()
        return

    def get_rss(self):
        ''' Syncs rss feed from imdb with library
        rss_url (str): url of rss feed

        Gets raw rss, sends to self.parse_xml to turn into dict

        Sends parsed xml to self.sync_new_movies

        Does not return
        '''

        try:
            record = json.loads(core.sql.system('imdb_sync_record'))
        except Exception as e:
            record = {}

        for url in core.CONFIG['Search']['Watchlists']['imdbrss']:
            movies = []
            if 'rss' not in url:
                logging.warning('Invalid IMDB RSS feed: {}'.format(url))
                continue

            list_id = ''.join(filter(str.isdigit, url))
            logging.info('Syncing rss IMDB watchlist {}'.format(url))
            try:
                response = Url.open(url).text
            except Exception as e:
                logging.error('IMDB rss request.', exc_info=True)
                continue

            last_sync = record.get(list_id) or 'Sat, 01 Jan 2000 00:00:00 GMT'
            last_sync = datetime.strptime(last_sync, self.date_format)

            record[list_id] = self.parse_build_date(response)

            logging.debug('Last IMDB sync time: {}'.format(last_sync))

            for i in self.parse_xml(response):
                pub_date = datetime.strptime(i['pubDate'], self.date_format)

                if last_sync >= pub_date:
                    break
                else:
                    if i not in movies:
                        title = i['title']
                        imdbid = i['imdbid'] = i['link'].split('/')[-2]
                        movies.append(i)
                        logging.info('Found new watchlist movie: {} {}'.format(title, imdbid))

            if movies:
                logging.info('Found {} movies in watchlist {}.'.format(len(movies), list_id))
                self.sync_new_movies(movies, list_id)

        logging.info('Storing last synced date.')
        if core.sql.row_exists('SYSTEM', name='imdb_sync_record'):
            core.sql.update('SYSTEM', 'data', json.dumps(record), 'name', 'imdb_sync_record')
        else:
            core.sql.write('SYSTEM', {'data': json.dumps(record), 'name': 'imdb_sync_record'})
        logging.info('IMDB sync complete.')

    def parse_xml(self, feed):
        ''' Turns rss into python dict
        feed (str): rss feed text

        Returns list of dicts of movies in rss
        '''

        root = ET.fromstring(feed)

        # This so ugly, but some newznab sites don't output json.
        items = []
        for item in root.iter('item'):
            d = {}
            for i_c in item:
                d[i_c.tag] = i_c.text
            items.append(d)
        return items

    def parse_build_date(self, feed):
        ''' Gets lastBuildDate from imdb rss
        feed (str): str xml feed

        Last build date is used as a stopping point when iterating over the rss.
            There is no need to check movies twice since they will be removed anyway
            when checking if it already exists in the library.

        Returns str last build date from rss
        '''

        root = ET.fromstring(feed)

        for i in root.iter('lastBuildDate'):
            return i.text

    def sync_new_movies(self, new_movies, list_id):
        ''' Adds new movies from rss feed
        new_movies (list): dicts of movies
        list_id (str): id # of watch list

        Checks last sync time and pulls new imdbids from feed.

        Checks if movies are already in library and ignores.

        Executes ajax.add_wanted_movie() for each new imdbid

        Does not return
        '''

        existing_movies = [i['imdbid'] for i in core.sql.get_user_movies()]

        movies_to_add = [i for i in new_movies if i['imdbid'] not in existing_movies]

        # do quick-add procedure
        for movie in movies_to_add:
            imdbid = movie['imdbid']
            movie = self.tmdb._search_imdbid(imdbid)
            if not movie:
                logging.warning('{} not found on TMDB. Cannot add.'.format(imdbid))
                continue
            else:
                movie = movie[0]
            logging.info('Adding movie {} {} from imdb watchlist.'.format(movie['title'], movie['imdbid']))
            movie['year'] = movie['release_date'][:4]
            movie['origin'] = 'IMDB'

            added = core.manage.add_movie(movie)
            if added['response'] and core.CONFIG['Search']['searchafteradd']:
                self.searcher.search(imdbid, movie['title'], movie['year'], 'Default')

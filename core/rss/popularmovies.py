from core import ajax, sqldb
from core.movieinfo import TMDB
from core.helpers import Url
import json
import logging
import time

logging = logging.getLogger(__name__)


class PopularMoviesFeed(object):
    def __init__(self):
        self.tmdb = TMDB()
        self.sql = sqldb.SQL()
        self.ajax = ajax.Ajax()
        return

    def get_feed(self):
        ''' Gets feed from popular-movies (https://github.com/sjlu/popular-movies)

        Gets raw feed (JSON), sends to self.parse_xml to turn into dict

        Returns True or None on success or failure (due to exception or empty movie list)
        '''

        movies = None

        logging.info('Syncing popular movie feed.')

        try:
            movies = json.loads(Url.open('https://s3.amazonaws.com/popular-movies/movies.json').text)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Popular feed request failed.', exc_info=True)
            return None

        if movies:
            logging.info('Found {} movies in popular movies.'.format(len(movies)))
            self.sync_new_movies(movies)
            logging.info('Popular movies sync complete.')
            return True
        else:
            return None

    def sync_new_movies(self, movies):
        ''' Adds new movies from rss feed
        :params movies: list of dicts of movies

        Checks last sync time and pulls new imdbids from feed.

        Checks if movies are already in library and ignores.

        Executes ajax.add_wanted_movie() for each new imdbid

        Does not return
        '''

        new_sync_movies = []
        for i in movies:

            title = i['title']
            imdbid = i['imdb_id']

            logging.info('Found new watchlist movie: {} {}'.format(title, imdbid))

            new_sync_movies.append(imdbid)

        # check if movies already exists

        existing_movies = [i['imdbid'] for i in self.sql.get_user_movies()]

        movies_to_add = [i for i in new_sync_movies if i not in existing_movies]

        # do quick-add procedure
        for imdbid in movies_to_add:
            movie_info = self.tmdb._search_imdbid(imdbid)[0]
            if not movie_info:
                logging.warning('{} not found on TMDB. Cannot add.'.format(imdbid))
                continue
            movie_info['quality'] = 'Default'
            self.ajax.add_wanted_movie(json.dumps(movie_info))
            time.sleep(1)

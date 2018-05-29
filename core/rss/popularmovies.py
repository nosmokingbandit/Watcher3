import core
from core import searcher
from core.movieinfo import TheMovieDatabase
from core.library import Manage
from core.helpers import Url
import json
import logging

logging = logging.getLogger(__name__)


def sync_feed():
    ''' Gets feed from popular-movies (https://github.com/sjlu/popular-movies)

    Gets raw feed (JSON) and adds all new movies with _sync_new_movies

    Returns bool
    '''

    movies = None

    logging.info('Syncing Steven Lu\'s popular movie feed.')

    try:
        movies = json.loads(Url.open('https://s3.amazonaws.com/popular-movies/movies.json').text)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('Popular feed request failed.', exc_info=True)
        return False

    if movies:
        logging.info('Found {} movies in popular movies.'.format(len(movies)))
        _sync_new_movies(movies)
        logging.info('Popular movies sync complete.')
        return True
    else:
        return False


def _sync_new_movies(movies):
    ''' Adds new movies from rss feed
    movies (list): dicts of movies

    Checks last sync time and pulls new imdbids from feed.

    Checks if movies are already in library and ignores.

    Executes ajax.add_wanted_movie() for each new imdbid

    Does not return
    '''

    existing_movies = [i['imdbid'] for i in core.sql.get_user_movies()]

    movies_to_add = [i for i in movies if i['imdb_id'] not in existing_movies]

    # do quick-add procedure
    for movie in movies_to_add:
        imdbid = movie['imdb_id']
        movie = TheMovieDatabase._search_imdbid(imdbid)
        if not movie:
            logging.warning('{} not found on TMDB. Cannot add.'.format(imdbid))
            continue
        else:
            movie = movie[0]
        logging.info('Adding movie {} {} from PopularMovies list.'.format(movie['title'], movie['imdbid']))
        movie['quality'] = 'Default'
        movie['origin'] = 'PopularMovies'
        added = Manage.add_movie(movie)

        if added['response'] and core.CONFIG['Search']['searchafteradd'] and movie['year'] != 'N/A':
            searcher.search(imdbid, movie['title'], movie['year'], movie['quality'])

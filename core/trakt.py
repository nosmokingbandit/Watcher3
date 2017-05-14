from core.helpers import Url
from core.helpers import Comparisons
import json
import core
from core import library, searcher, sqldb

import logging
logging = logging.getLogger(__name__)


class Trakt(object):

    def __init__(self):
        self.sql = sqldb.SQL()
        self.library = library.Manage()
        self.searcher = searcher.Searcher()
        return

    def trakt_sync(self):
        ''' Syncs all enabled Trakt lists

        Gets list of movies from each enabled Trakt lists

        Adds missing movies to library as Waiting/Default

        Returns bool for success/failure
        '''

        success = True

        min_score = core.CONFIG['Search']['Watchlists']['traktscore']
        length = core.CONFIG['Search']['Watchlists']['traktlength']
        movies = []

        for k, v in core.CONFIG['Search']['Watchlists']['Traktlists'].items():
            if v is False:
                continue
            movies += [i for i in self.get_list(k, min_score=min_score, length=length) if i not in movies]

        logging.info('Found {} movies from Trakt lists.'.format(len(movies)))

        library = [i['imdbid'] for i in self.sql.get_user_movies()]

        movies = [i for i in movies if i['ids']['imdb'] not in library]

        for i in movies:
            imdbid = i['ids']['imdb']
            logging.info('Adding movie {} {} from Trakt'.format(i['title'], imdbid))
            added = self.library.add_movie({'id': i['ids']['tmdb']})
            if added['response'] and core.CONFIG['Search']['searchafteradd']:
                self.searcher.search(imdbid, i['title'], i['year'], 'Default')

        return success

    def get_list(self, list_name, min_score=0, length=10):
        ''' Gets list of trending movies from Trakt
        list_name: str name of Trakt list. Must be one of
            ('trending', 'popular', 'watched', 'collected', 'anticipated', 'boxoffice')
        min_score: float minimum score to accept (max 10)   <default 0>
        length: int how many results to get from Trakt      <default 10>

        Length is applied before min_score, so actual result count
            can be less than length

        Returns list of dicts of movie info
        '''

        headers = {'Content-Type': 'application/json',
                   'trakt-api-version': '2',
                   'trakt-api-key': Comparisons._k(b'trakt')
                   }

        if list_name not in ('trending', 'popular', 'watched', 'collected', 'anticipated', 'boxoffice'):
            logging.error('Invalid list_name {}'.format(list_name))
            return []

        logging.info('Getting Trakt list {}'.format(list_name))
        url = 'https://api.trakt.tv/movies/{}/?extended=full'.format(list_name)

        try:
            r = Url.open(url, headers=headers)
            if r.status_code != 200:
                return []
            m = json.loads(r.text)[:length]
            if list_name == 'popular':
                return [i for i in m if i['rating'] >= min_score]
            return [i['movie'] for i in m if i['movie']['rating'] >= min_score]

        except Exception as e:
            logging.error('Unable to get Trakt list.', exc_info=True)
            return []

import core
from core import searcher
from core.movieinfo import TheMovieDatabase
from core.library import Manage
from core.helpers import Url
from datetime import datetime
import json
import logging
import os
import csv

logging = logging.getLogger(__name__)


data_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'imdb')
date_format = '%Y-%m-%d'


def sync():
    ''' Syncs CSV lists from IMDB

    Does not return
    '''

    movies_to_add = []
    library = [i[2] for i in core.sql.quick_titles()]

    try:
        record = json.loads(core.sql.system('imdb_sync_record'))
    except Exception as e:
        record = {}

    for url in core.CONFIG['Search']['Watchlists']['imdbcsv']:
        if url[-6:] not in ('export', 'export/'):
            logging.warning('{} does not look like a valid imdb list'.format(url))
            continue

        list_id = 'ls' + ''.join(filter(str.isdigit, url))
        logging.info('Syncing rss IMDB watchlist {}'.format(list_id))

        last_sync = datetime.strptime((record.get(list_id) or '2000-01-01'), date_format)

        try:
            csv_text = Url.open(url).text
            watchlist = [dict(i) for i in csv.DictReader(csv_text.splitlines())][::-1]

            record[list_id] = watchlist[0]['Created']

            for movie in watchlist:
                pub_date = datetime.strptime(movie['Created'], date_format)

                if last_sync > pub_date:
                    break

                imdbid = movie['Const']
                if imdbid not in library and imdbid not in movies_to_add:
                    logging.info('Found new watchlist movie {}'.format(movie['Title']))
                    movies_to_add.append(imdbid)

        except Exception as e:
            logging.warning('Unable to sync list {}'.format(list_id))

    m = []
    for imdbid in movies_to_add:
        movie = TheMovieDatabase._search_imdbid(imdbid)
        if not movie:
            logging.warning('{} not found on TheMovieDB. Cannot add.'.format(imdbid))
            continue
        else:
            movie = movie[0]
        logging.info('Adding movie {} {} from IMDB watchlist.'.format(movie['title'], movie['imdbid']))
        movie['year'] = movie['release_date'][:4] if movie.get('release_date') else 'N/A'
        movie['origin'] = 'IMDB'

        added = Manage.add_movie(movie)
        if added['response']:
            m.append((imdbid, movie['title'], movie['year']))

    if core.CONFIG['Search']['searchafteradd']:
        for i in m:
            if i[2] != 'N/A':
                searcher.search(i[0], i[1], i[2], core.config.default_profile())

    logging.info('Storing last synced date.')
    if core.sql.row_exists('SYSTEM', name='imdb_sync_record'):
        core.sql.update('SYSTEM', 'data', json.dumps(record), 'name', 'imdb_sync_record')
    else:
        core.sql.write('SYSTEM', {'data': json.dumps(record), 'name': 'imdb_sync_record'})
    logging.info('IMDB sync complete.')

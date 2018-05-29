from core.helpers import Url
from core.helpers import Comparisons
from core.library import Manage
import json
import core
import datetime
from core import searcher
import xml.etree.cElementTree as ET
import re

import logging
logging = logging.getLogger(__name__)


searcher = searcher
date_format = '%a, %d %b %Y %H:%M:%S'
trakt_date_format = '%Y-%m-%dT%H:%M:%S'


def sync():
    ''' Syncs all enabled Trakt lists and rss lists

    Gets list of movies from each enabled Trakt lists

    Adds missing movies to library as Waiting/Default

    Returns bool for success/failure
    '''

    logging.info('Syncing Trakt lists.')

    success = True

    min_score = core.CONFIG['Search']['Watchlists']['traktscore']
    length = core.CONFIG['Search']['Watchlists']['traktlength']
    movies = []

    if core.CONFIG['Search']['Watchlists']['traktrss']:
        sync_rss()

    for k, v in core.CONFIG['Search']['Watchlists']['Traktlists'].items():
        if v is False:
            continue
        movies += [i for i in get_list(k, min_score=min_score, length=length) if i not in movies]

    library = [i['imdbid'] for i in core.sql.get_user_movies()]

    movies = [i for i in movies if i['ids']['imdb'] not in library]

    logging.info('Found {} new movies from Trakt lists.'.format(len(movies)))

    for i in movies:
        imdbid = i['ids']['imdb']
        logging.info('Adding movie {} {} from Trakt'.format(i['title'], imdbid))

        added = Manage.add_movie({'id': i['ids']['tmdb'],
                                  'imdbid': i['ids']['imdb'],
                                  'title': i['title'],
                                  'origin': 'Trakt'})
        if added['response'] and core.CONFIG['Search']['searchafteradd'] and i['year'] != 'N/A':
            searcher.search(imdbid, i['title'], i['year'], core.config.default_profile())

    return success


def sync_rss():
    ''' Gets list of new movies in user's rss feed(s)

    Returns list of movie dicts
    '''

    try:
        record = json.loads(core.sql.system('trakt_sync_record'))
    except Exception as e:
        record = {}

    for url in core.CONFIG['Search']['Watchlists']['traktrss'].split(','):
        list_id = url.split('.atom')[0].split('/')[-1]

        last_sync = record.get(list_id) or 'Sat, 01 Jan 2000 00:00:00'
        last_sync = datetime.datetime.strptime(last_sync, date_format)

        logging.info('Syncing Trakt RSS watchlist {}. Last sync: {}'.format(list_id, last_sync))
        try:
            feed = Url.open(url).text
            feed = re.sub(r'xmlns=".*?"', r'', feed)
            root = ET.fromstring(feed)
        except Exception as e:
            logging.error('Trakt rss request.', exc_info=True)
            continue

        d = root.find('updated').text[:19]

        do = datetime.datetime.strptime(d, trakt_date_format)
        record[list_id] = datetime.datetime.strftime(do, date_format)

        for entry in root.iter('entry'):
            try:
                pub = datetime.datetime.strptime(entry.find('published').text[:19], trakt_date_format)
                if last_sync >= pub:
                    break
                else:
                    t = entry.find('title').text

                    title = ' ('.join(t.split(' (')[:-1])

                    year = ''
                    for i in t.split(' (')[-1]:
                        if i.isdigit():
                            year += i
                    year = int(year)

                    logging.info('Searching TheMovieDatabase for {} {}'.format(title, year))
                    movie = Manage.tmdb._search_title('{} {}'.format(title, year))[0]
                    if movie:
                        movie['origin'] = 'Trakt'
                        logging.info('Found new watchlist movie {} {}'.format(title, year))

                        r = Manage.add_movie(movie)

                        if r['response'] and core.CONFIG['Search']['searchafteradd'] and movie['year'] != 'N/A':
                            searcher.search(movie['imdbid'], movie['title'], movie['year'], core.config.default_profile())
                    else:
                        logging.warning('Unable to find {} {} on TheMovieDatabase'.format(title, year))

            except Exception as e:
                logging.error('Unable to parse Trakt RSS list entry.', exc_info=True)

    logging.info('Storing last synced date.')
    if core.sql.row_exists('SYSTEM', name='trakt_sync_record'):
        core.sql.update('SYSTEM', 'data', json.dumps(record), 'name', 'trakt_sync_record')
    else:
        core.sql.write('SYSTEM', {'data': json.dumps(record), 'name': 'trakt_sync_record'})

    logging.info('Trakt RSS sync complete.')


def get_list(list_name, min_score=0, length=10):
    ''' Gets list of trending movies from Trakt
    list_name (str): name of Trakt list. Must be one of ('trending', 'popular', 'watched', 'collected', 'anticipated', 'boxoffice')
    min_score (float): minimum score to accept (max 10)   <optional - default 0>
    length (int): how many results to get from Trakt      <optional - default 10>

    Length is applied before min_score, so actual result count
        can be less than length

    Returns list of dicts of movie info
    '''

    logging.info('Getting Trakt list {}'.format(list_name))

    headers = {'Content-Type': 'application/json',
               'trakt-api-version': '2',
               'trakt-api-key': Comparisons._k(b'trakt')
               }

    if list_name not in ('trending', 'popular', 'watched', 'collected', 'anticipated', 'boxoffice'):
        logging.error('Invalid list_name {}'.format(list_name))
        return []

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

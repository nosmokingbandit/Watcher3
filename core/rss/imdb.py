import core
from core import library, searcher
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
        self.library = library.Manage()
        self.searcher = searcher.Searcher()
        return

    def get_rss(self):
        ''' Gets rss feed from imdb
        :param rss_url: str url to rss feed

        Gets raw rss, sends to self.parse_xml to turn into dict

        Returns True or None on success or failure (due to exception or empty movie list)
        '''

        movies = []
        for url in core.CONFIG['Search']['Watchlists']['imdbrss']:
            if 'rss' not in url:
                continue

            list_id = ''.join(filter(str.isdigit, url))
            logging.info('Syncing rss IMDB watchlist {}'.format(url))
            try:
                response = Url.open(url).text
            except Exception as e: # noqa
                logging.error('IMDB rss request.', exc_info=True)
                continue

            lastbuilddate = self.parse_build_date(response)

            if os.path.isfile(self.data_file):
                with open(self.data_file, 'r') as f:
                    last_sync = json.load(f).get(list_id) or 'Sat, 01 Jan 2000 00:00:00 GMT'
            else:
                last_sync = 'Sat, 01 Jan 2000 00:00:00 GMT'

            last_sync = datetime.strptime(last_sync, self.date_format)

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

            logging.info('Storing last synced date.')
            if os.path.isfile(self.data_file):
                with open(self.data_file, 'r+') as f:
                    date_log = json.load(f)
                    date_log[list_id] = lastbuilddate
                    f.seek(0)
                    json.dump(date_log, f)
            else:
                with open(self.data_file, 'w') as f:
                    date_log = {list_id: lastbuilddate}
                    json.dump(date_log, f)

            if movies:
                lastbuilddate = self.parse_build_date(response)
                logging.info('Found {} movies in watchlist {}.'.format(len(movies), list_id))
                self.sync_new_movies(movies, list_id, lastbuilddate)

        logging.info('IMDB sync complete.')

    def parse_xml(self, feed):
        ''' Turns rss into python dict
        :param feed: str rss feed

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
        :param feed: str xml feed

        Last build date is used as a stopping point when iterating over the rss.
            There is no need to check movies twice since they will be removed anyway
            when checking if it already exists in the library.

        Returns str last build date from rss
        '''

        root = ET.fromstring(feed)

        for i in root.iter('lastBuildDate'):
            return i.text

    def sync_new_movies(self, new_movies, list_id, lastbuilddate):
        ''' Adds new movies from rss feed
        new_movies: list of dicts of movies
        list_id: str id # of watch list

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
            movie_info = self.tmdb._search_imdbid(imdbid)[0]
            if not movie_info:
                logging.warning('{} not found on TMDB. Cannot add.'.format(imdbid))
                continue
            logging.info('Adding movie {} {} from imdb watchlist.'.format(movie['title'], movie['imdbid']))
            movie_info['year'] = movie_info['release_date'][:4]

            added = self.library.add_movie(movie_info, origin='IMDB')
            if added['response'] and core.CONFIG['Search']['searchafteradd']:
                self.searcher.search(imdbid, movie_info['title'], movie_info['year'], 'Default')

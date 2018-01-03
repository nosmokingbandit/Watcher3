import datetime
import logging

import cherrypy
import core
import os
import time
from base64 import b16encode

from core import searcher, postprocessing
from core.rss import imdb, popularmovies
from core.cp_plugins.taskscheduler import SchedulerPlugin
from core import trakt
from core.library import Metadata

logging = logging.getLogger(__name__)

md = Metadata()
pp = postprocessing.Postprocessing()
search = searcher.Searcher()
imdb = imdb.ImdbRss()
popular_feed = popularmovies.PopularMoviesFeed()
trakt = trakt.Trakt()


def create_plugin():
    ''' Creates plugin instance, adds tasks, and subscribes to cherrypy.engine

    Does not return
    '''
    logging.info('Initializing scheduler plugin.')
    core.scheduler_plugin = SchedulerPlugin(cherrypy.engine, record_handler=record_handler)
    AutoSearch.create()
    AutoUpdateCheck.create()
    ImdbRssSync.create()
    MetadataUpdate.create()
    PopularMoviesSync.create()
    PostProcessingScan.create()
    TraktSync.create()
    core.scheduler_plugin.subscribe()


class record_handler(object):
    @staticmethod
    def read():
        return {i['name']: {'last_execution': i['last_execution']} for i in core.sql.dump('TASKS')}

    @staticmethod
    def write(name, le):
        if core.sql.row_exists('TASKS', name=name):
            core.sql.update('TASKS', 'last_execution', le, 'name', name)
        else:
            core.sql.write('TASKS', {'last_execution': le, 'name': name})
        return


class PostProcessingScan(object):
    ''' Scheduled task to automatically scan directory for movie to process '''
    @staticmethod
    def create():
        conf = core.CONFIG['Postprocessing']['Scanner']
        interval = conf['interval'] * 60

        now = datetime.datetime.today()
        hr = now.hour
        minute = now.minute + interval

        SchedulerPlugin.ScheduledTask(hr, minute, interval, PostProcessingScan.scan_directory, auto_start=conf['enabled'], name='PostProcessing Scan')
        return

    @staticmethod
    def scan_directory():
        ''' Method to scan directory for movies to process '''

        conf = core.CONFIG['Postprocessing']['Scanner']
        d = conf['directory']

        logging.info('Scanning {} for movies to process.'.format(d))

        minsize = core.CONFIG['Postprocessing']['Scanner']['minsize'] * 1048576

        if conf['newfilesonly']:
            t = core.scheduler_plugin.record.get('PostProcessing Scan', {}).get('last_execution')
            if not t:
                logging.warning('Unable to scan directory, last scan timestamp unknown.')
                return
            le = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
            threshold = time.mktime(le.timetuple())

            logging.info('Scanning for new files only (last scan: {}).'.format(d, le))
            files = [os.path.join(d, i) for i in os.listdir(d) if os.path.getmtime(os.path.join(d, i)) > threshold and os.path.getsize(os.path.join(d, i)) > minsize]
        else:
            files = [os.path.join(d, i) for i in os.listdir(d) if os.path.getsize(os.path.join(d, i)) > minsize]

        if not files:
            logging.info('No new files found in directory scan.')
            return

        for i in files:
            while i[-1] in ('\\', '/'):
                i = i[:-1]
            fname = os.path.basename(i)

            logging.info('Processing {}.'.format(i))

            r = core.sql.get_single_search_result('title', fname)
            if r:
                logging.info('Found match for {} in releases: {}.'.format(fname, r['title']))
            else:
                r['guid'] = 'POSTPROCESSING{}'.format(b16encode(fname.encode('ascii', errors='ignore')).decode('utf-8').zfill(16)[:16])
                logging.info('Unable to find match in database for {}, release cannot be marked as Finished.'.format(fname))

            d = {'apikey': core.CONFIG['Server']['apikey'],
                 'mode': 'complete',
                 'path': i,
                 'guid': r.get('guid') or '',
                 'downloadid': ''
                 }

            pp.default(**d)


class AutoSearch(object):
    ''' Scheduled task to automatically run search/snatch methods '''
    @staticmethod
    def create():
        interval = core.CONFIG['Search']['rsssyncfrequency'] * 60

        now = datetime.datetime.today()
        hr = now.hour
        min = now.minute + core.CONFIG['Search']['rsssyncfrequency']

        SchedulerPlugin.ScheduledTask(hr, min, interval, search.search_all, auto_start=True, name='Movie Search')


class MetadataUpdate(object):
    ''' Scheduled task to automatically run metadata updater '''

    @staticmethod
    def create():
        interval = 72 * 60 * 60  # 72 hours

        now = datetime.datetime.today()

        hr = now.hour
        min = now.minute

        SchedulerPlugin.ScheduledTask(hr, min, interval, MetadataUpdate.metadata_update, auto_start=True, name='Metadata Update')
        return

    @staticmethod
    def metadata_update():
        ''' Updates metadata for library

        If movie's theatrical release is more than a year ago it is ignored.

        Checks movies with a missing 'media_release_date' field. By the time
            this field is filled all other fields should be populated.

        '''
        logging.info('Updating library metadata.')

        movies = core.sql.get_user_movies()

        cutoff = datetime.datetime.today() - datetime.timedelta(days=365)

        u = []
        for i in movies:
            if i['release_date'] and datetime.datetime.strptime(i['release_date'], '%Y-%m-%d') < cutoff:
                continue

            if not i['media_release_date'] and i['status'] not in ('Finished', 'Disabled'):
                u.append(i)

        if not u:
            return

        logging.info('Updating metadata for: {}.'.format(', '.join([i['title'] for i in u])))

        for i in u:
            md.update(i.get('imdbid'), tmdbid=i.get('tmdbid'), force_poster=False)

        return


class AutoUpdateCheck(object):
    ''' Scheduled task to automatically check git for updates and install '''
    @staticmethod
    def create():

        interval = core.CONFIG['Server']['checkupdatefrequency'] * 3600

        now = datetime.datetime.today()
        hr = now.hour
        min = now.minute + (core.CONFIG['Server']['checkupdatefrequency'] * 60)
        if now.second > 30:
            min += 1

        if core.CONFIG['Server']['checkupdates']:
            auto_start = True
        else:
            auto_start = False

        SchedulerPlugin.ScheduledTask(hr, min, interval, AutoUpdateCheck.update_check, auto_start=auto_start, name='Update Checker')
        return

    @staticmethod
    def update_check(install=True):
        ''' Checks for any available updates
        install (bool): install updates if found

        Setting 'install' for False will ignore user's config for update installation
        If 'install' is True, user config must also allow automatic updates

        Creates notification if updates are available.

        Returns dict from core.updater.update_check():
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        return core.updater.update_check(install=install)


class ImdbRssSync(object):
    ''' Scheduled task to automatically sync IMDB watchlists '''
    @staticmethod
    def create():
        interval = core.CONFIG['Search']['Watchlists']['imdbfrequency'] * 60
        now = datetime.datetime.today()

        hr = now.hour
        min = now.minute + core.CONFIG['Search']['Watchlists']['imdbfrequency']

        if core.CONFIG['Search']['Watchlists']['imdbsync']:
            auto_start = True
        else:
            auto_start = False

        SchedulerPlugin.ScheduledTask(hr, min, interval, imdb.get_rss, auto_start=auto_start, name='IMDB Sync')
        return


class PopularMoviesSync(object):
    ''' Scheduled task to automatically sync PopularMovies list '''
    @staticmethod
    def create():
        interval = 24 * 3600

        hr = core.CONFIG['Search']['Watchlists']['popularmovieshour']
        min = core.CONFIG['Search']['Watchlists']['popularmoviesmin']

        if core.CONFIG['Search']['Watchlists']['popularmoviessync']:
            auto_start = True
        else:
            auto_start = False

        SchedulerPlugin.ScheduledTask(hr, min, interval, popular_feed.get_feed, auto_start=auto_start, name='PopularMovies Sync')
        return


class TraktSync(object):
    ''' Scheduled task to automatically sync selected Trakt lists '''

    @staticmethod
    def create():
        interval = core.CONFIG['Search']['Watchlists']['traktfrequency'] * 60

        now = datetime.datetime.today()

        hr = now.hour
        min = now.minute + core.CONFIG['Search']['Watchlists']['traktfrequency']

        if core.CONFIG['Search']['Watchlists']['traktsync']:
            if any(core.CONFIG['Search']['Watchlists']['Traktlists'].keys()):
                auto_start = True
            else:
                logging.warning('Trakt sync enabled but no lists are enabled.')
                auto_start = False
        else:
            auto_start = False

        SchedulerPlugin.ScheduledTask(hr, min, interval, trakt.trakt_sync, auto_start=auto_start, name='Trakt Sync')
        return

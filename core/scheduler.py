import datetime
import logging

import cherrypy
import core
import glob
import hashlib
import os
import time
from base64 import b16encode

from core import searcher, version, notification, postprocessing
from core.rss import imdb, popularmovies
from core.cp_plugins import taskscheduler
from core import trakt
from core.library import Metadata

logging = logging.getLogger(__name__)

ver = version.Version()
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
    core.scheduler_plugin = taskscheduler.SchedulerPlugin(cherrypy.engine)
    AutoSearch.create()
    AutoUpdateCheck.create()
    ImdbRssSync.create()
    MetadataUpdate.create()
    PopularMoviesSync.create()
    PostProcessingScan.create()
    TraktSync.create()
    core.scheduler_plugin.subscribe()


def restart_scheduler(diff):
    ''' Restarts and scheduled tasks in diff
    diff (dict): modified keys in config file

    Reads diff and determines which tasks need to be restart_scheduler

    Does not return
    '''

    now = datetime.datetime.today()

    if 'Server' in diff:
        d = diff['Server'].keys()

        if any(i in d for i in ('checkupdates', 'checkupdatefrequency')):
            hr = now.hour + core.CONFIG['Server']['checkupdatefrequency']
            min = now.minute
            interval = core.CONFIG['Server']['checkupdatefrequency'] * 3600
            auto_start = core.CONFIG['Server']['checkupdates']
            taskscheduler.SchedulerPlugin.task_list['Update Checker'].reload(hr, min, interval, auto_start=auto_start)

    if 'Search' in diff:
        d = diff['Search'].keys()
        if 'rsssyncfrequency' in d:
            hr = now.hour
            min = now.minute + core.CONFIG['Search']['rsssyncfrequency']
            interval = core.CONFIG['Search']['rsssyncfrequency'] * 60
            auto_start = True
            taskscheduler.SchedulerPlugin.task_list['Movie Search'].reload(hr, min, interval, auto_start=auto_start)

        if 'Watchlists' in d:
            d = diff['Search']['Watchlists'].keys()
            if any(i in d for i in ('imdbfrequency', 'imdbsync')):
                hr = now.hour
                min = now.minute + core.CONFIG['Search']['Watchlists']['imdbfrequency']
                interval = core.CONFIG['Search']['Watchlists']['imdbfrequency'] * 60
                auto_start = core.CONFIG['Search']['Watchlists']['imdbsync']
                taskscheduler.SchedulerPlugin.task_list['IMDB Sync'].reload(hr, min, interval, auto_start=auto_start)

            if any(i in d for i in ('popularmoviessync', 'popularmovieshour', 'popularmoviesmin')):
                hr = core.CONFIG['Search']['Watchlists']['popularmovieshour']
                min = core.CONFIG['Search']['Watchlists']['popularmoviesmin']
                interval = 24 * 3600
                auto_start = core.CONFIG['Search']['Watchlists']['popularmoviessync']
                taskscheduler.SchedulerPlugin.task_list['PopularMovies Sync'].reload(hr, min, interval, auto_start=auto_start)

            if any(i in d for i in ('traktsync', 'traktfrequency')):
                hr = now.hour
                min = now.minute + core.CONFIG['Search']['Watchlists']['traktfrequency']
                interval = core.CONFIG['Search']['Watchlists']['traktfrequency'] * 60
                auto_start = core.CONFIG['Search']['Watchlists']['traktsync']
                taskscheduler.SchedulerPlugin.task_list['Trakt Sync'].reload(hr, min, interval, auto_start=auto_start)

    if 'Postprocessing' in diff:
        d = diff['Postprocessing'].get('Scanner', {})
        if any(i in d for i in ('interval', 'enabled')):
            hr = now.hour
            min = now.minute + core.CONFIG['Postprocessing']['Scanner']['interval']
            interval = core.CONFIG['Postprocessing']['Scanner']['interval'] * 60
            auto_start = core.CONFIG['Postprocessing']['Scanner']['enabled']
            taskscheduler.SchedulerPlugin.task_list['PostProcessing Scan'].reload(hr, min, interval, auto_start=auto_start)


class PostProcessingScan(object):
    ''' Scheduled task to automatically scan directory for movie to process '''
    @staticmethod
    def create():
        conf = core.CONFIG['Postprocessing']['Scanner']
        interval = conf['interval'] * 60

        now = datetime.datetime.today()
        hr = now.hour
        minute = now.minute + interval

        taskscheduler.ScheduledTask(hr, minute, interval, PostProcessingScan.scan_directory, auto_start=conf['enabled'], name='PostProcessing Scan')
        return

    @staticmethod
    def scan_directory():
        ''' Method to scan directory for movies to process '''

        conf = core.CONFIG['Postprocessing']['Scanner']
        d = conf['directory']

        logging.info('Scanning {} for movies to process.'.format(d))

        if conf['newfilesonly']:
            t = core.scheduler_plugin.record.get('PostProcessing Scan', {}).get('lastexecution')
            if not t:
                logging.warning('Unable to scan directory, last scan timestamp unknown.')
                return
            le = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
            threshold = time.mktime(le.timetuple())

            logging.info('Scanning for new files only (last scan: {}).'.format(d, le))
            files = [os.path.join(d, i) for i in os.listdir(d) if os.path.join(d, i).getmtime() > threshold]
        else:
            files = [os.path.join(d, i) for i in os.listdir(d)]

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
                 'guid': r.get('guid', ''),
                 'downloadid': ''
                 }

            pp.POST(**d)


class AutoSearch(object):
    ''' Scheduled task to automatically run search/snatch methods '''
    @staticmethod
    def create():
        interval = core.CONFIG['Search']['rsssyncfrequency'] * 60

        now = datetime.datetime.today()
        hr = now.hour
        min = now.minute + core.CONFIG['Search']['rsssyncfrequency']

        task_search = taskscheduler.ScheduledTask(hr, min, interval, search.search_all, auto_start=True, name='Movie Search')

        # update core.NEXT_SEARCH
        delay = task_search.delay
        now = now.replace(second=0, microsecond=0)
        core.NEXT_SEARCH = now + datetime.timedelta(0, delay)


class MetadataUpdate(object):
    ''' Scheduled task to automatically run metadata updater '''

    @staticmethod
    def create():
        interval = 72 * 60 * 60  # 72 hours

        now = datetime.datetime.today()

        hr = now.hour
        min = now.minute

        taskscheduler.ScheduledTask(hr, min, interval, MetadataUpdate.metadata_update, auto_start=True, name='Metadata Update')
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

        ''' This if block can be removed later
        Removes old 'missing_poster' images and updates database 'poster' field
        '''

        clean_file = os.path.join(core.PROG_PATH, 'static/images/posters/.clean')

        if not os.path.isfile(clean_file):
            posters = glob.glob(os.path.join(core.PROG_PATH, 'static/images/posters/*.jpg'))
            for i in posters:
                try:
                    with open(i, 'rb') as f:
                        f.seek(-512, 2)
                        data = f.read()
                        h = hashlib.md5(data).hexdigest()
                        if h in ('f4e996b087b509f4507a05863f9e9970', '367c8a3a111a46efb608b481936197a7'):
                            imdbid = 'tt{}'.format(i.split('tt')[-1][:-4])
                            core.sql.update('MOVIES', 'poster', None, 'imdbid', imdbid)
                            os.remove(i)
                except Exception as e:
                    continue

            with open(clean_file, 'a+'):
                pass
        ''' end removable block '''

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

        taskscheduler.ScheduledTask(hr, min, interval, AutoUpdateCheck.update_check, auto_start=auto_start, name='Update Checker')
        return

    @staticmethod
    def update_check(install=True):
        ''' Checks for any available updates
        install (bool): install updates if found

        Setting 'install' for False will ignore user's config for update installation
        If 'install' is True, user config must also allow automatic updates

        Creates notification if updates are available.

        Returns dict from core.version.Version.manager.update_check():
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        logging.info('Checking for updates.')

        return ver.manager.update_check()


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

        taskscheduler.ScheduledTask(hr, min, interval, imdb.get_rss, auto_start=auto_start, name='IMDB Sync')
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

        taskscheduler.ScheduledTask(hr, min, interval, popular_feed.get_feed, auto_start=auto_start, name='PopularMovies Sync')
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

        taskscheduler.ScheduledTask(hr, min, interval, trakt.trakt_sync, auto_start=auto_start, name='Trakt Sync')
        return

import datetime
import logging

import cherrypy
import core
import glob
import hashlib
import os

from core import searcher, version, notification
from core.rss import imdb, popularmovies
from core.cp_plugins import taskscheduler
from core import trakt
from core.library import Metadata

logging = logging.getLogger(__name__)

ver = version.Version()


def restart_scheduler(diff):
    ''' Restarts and scheduled tasks in diff
    diff: dict modified keys in config file

    Reads diff and determines which tasks need to be restart_scheduler

    Does not return
    '''

    now = datetime.datetime.now()
    if 'Server' in diff:
        d = diff['Server'].keys()

        if any(i in d for i in ('checkupdates', 'checkupdatefrequency')):
            hr = now.hour + core.CONFIG['Server']['checkupdatefrequency']
            min = now.minute
            interval = core.CONFIG['Server']['checkupdatefrequency'] * 3600
            auto_start = core.CONFIG['Server']['checkupdates']
            taskscheduler.SchedulerPlugin.task_list['update_check'].reload(hr, min, interval, auto_start=auto_start)

        if any(i in d for i in ('installupdates', 'installupdatehr', 'installupdatemin')):
            hr = core.CONFIG['Server']['installupdatehr']
            min = core.CONFIG['Server']['installupdatemin']
            interval = 24 * 3600
            auto_start = core.CONFIG['Server']['installupdates']
            taskscheduler.SchedulerPlugin.task_list['update_install'].reload(hr, min, interval, auto_start=auto_start)

    if 'Search' in diff:
        d = diff['Search'].keys()
        if 'rsssyncfrequency' in d:
            hr = now.hour
            min = now.minute + core.CONFIG['Search']['rsssyncfrequency']
            interval = core.CONFIG['Search']['rsssyncfrequency'] * 60
            auto_start = True
            taskscheduler.SchedulerPlugin.task_list['search_all'].reload(hr, min, interval, auto_start=auto_start)

        if 'Watchlists' in diff['Search']:
            d = diff['Search']['Watchlists'].keys()
            if any(i in d for i in ('imdbfrequency', 'imdsync')):
                hr = now.hour
                min = now.minute + core.CONFIG['Search']['Watchlists']['imdbfrequency']
                interval = core.CONFIG['Search']['Watchlists']['imdbfrequency'] * 60
                auto_start = core.CONFIG['Search']['Watchlists']['imdbsync']
                taskscheduler.SchedulerPlugin.task_list['imdb_sync'].reload(hr, min, interval, auto_start=auto_start)

            if any(i in d for i in ('popularmoviessync', 'popularmovieshour', 'popularmoviesmin')):
                hr = core.CONFIG['Search']['Watchlists']['popularmovieshour']
                min = core.CONFIG['Search']['Watchlists']['popularmoviesmin']
                interval = 24 * 3600
                auto_start = core.CONFIG['Search']['Watchlists']['popularmoviessync']
                taskscheduler.SchedulerPlugin.task_list['popularmovies_sync'].reload(hr, min, interval, auto_start=auto_start)

            if any(i in d for i in ('traktsync', 'traktfrequency')):
                hr = now.hour
                min = now.minute + core.CONFIG['Search']['Watchlists']['traktfrequency']
                interval = core.CONFIG['Search']['Watchlists']['traktfrequency'] * 60
                auto_start = core.CONFIG['Search']['Watchlists']['traktsync']
                taskscheduler.SchedulerPlugin.task_list['trakt_sync'].reload(hr, min, interval, auto_start=auto_start)
        else:
            return


class Scheduler(object):
    ''' Simple wrapper to create plugin instance

    '''

    def __init__(self):
        # create scheduler plugin
        self.plugin = taskscheduler.SchedulerPlugin(cherrypy.engine)


''' The following is all methods to create sheduled tasks.

Task creation need not be wrapped in a class, but a separate namespace helps
    make the code easier to read.

All task creation must create a new instance of ScheduledTask.
'''


class AutoSearch(object):
    @staticmethod
    def create():
        search = searcher.Searcher()
        interval = core.CONFIG['Search']['rsssyncfrequency'] * 60

        now = datetime.datetime.today()
        hr = now.hour
        min = now.minute + core.CONFIG['Search']['rsssyncfrequency']

        task_search = taskscheduler.ScheduledTask(hr, min, interval,
                                                  search.search_all,
                                                  auto_start=True)

        # update core.NEXT_SEARCH
        delay = task_search.delay
        now = datetime.datetime.today().replace(second=0, microsecond=0)
        core.NEXT_SEARCH = now + datetime.timedelta(0, delay)


class MetadataUpdate(object):

    md = Metadata()

    @staticmethod
    def create():
        interval = 72 * 60 * 60  # 72 hours

        now = datetime.datetime.now()

        hr = now.hour
        min = now.minute

        taskscheduler.ScheduledTask(hr, min, interval, MetadataUpdate.metadata_update,
                                    auto_start=True)
        return

    @staticmethod
    def metadata_update():
        ''' Updates metadata for library

        If movie's theatrical release is more than a year ago it is ignored.

        Checks movies with a missing 'media_release_date' field. By the time
            this field is filled all other fields should be populated.

        '''

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
                            core.SQL.update('MOVIES', 'poster', None, 'imdbid', imdbid)
                            os.remove(i)
                except Exception as e:
                    continue

            with open(clean_file, 'a+'):
                pass

        for i in movies:
            if i['release_date'] and datetime.datetime.strptime(i['release_date'], '%Y-%m-%d') < cutoff:
                continue

            if not i['media_release_date']:
                MetadataUpdate.md.update(i.get('imdbid'), tmdbid=i.get('tmdbid'))
        return


class AutoUpdateCheck(object):

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

        taskscheduler.ScheduledTask(hr, min, interval, AutoUpdateCheck.update_check,
                                    auto_start=auto_start)
        return

    @staticmethod
    def update_check():
        ''' Checks for any available updates

        Creates notification if updates are available.

        Returns dict from core.version.Version.manager.update_check():
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        ver = version.Version()

        data = ver.manager.update_check()
        # if data['status'] == 'current', nothing to do.
        if data['status'] == 'error':
            notif = {'title': 'Error Checking for Updates <br/>',
                     'message': data['error']
                     }
            notification.add(notif, type_='danger')

        elif data['status'] == 'behind':
            if data['behind_count'] == 1:
                title = '1 Update Available <br/>'
            else:
                title = '{} Updates Available <br/>'.format(data['behind_count'])

            compare = '{}/compare/{}...{}'.format(core.GIT_URL, data['local_hash'], data['new_hash'])

            notif = {'type': 'update',
                     'title': title,
                     'message': 'Click <a onclick="_start_update(event)"><u>here</u></a> to update now.<br/> Click <a href="{}" target="_blank"><u>here</u></a> to view changes.'.format(core.URL_BASE, compare)
                     }

            notification.add(notif, type_='primary')

            if core.CONFIG['Server']['installupdates']:
                logging.info('Currently {} commits behind. Updating to {}.'.format(core.UPDATE_STATUS['behind_count'], core.UPDATE_STATUS['new_hash']))

                core.UPDATING = True
                update = ver.manager.execute_update()
                core.UPDATING = False

                if not update:
                    logging.error('Update failed.')

                logging.info('Update successful, restarting.')
                cherrypy.engine.restart()
            else:
                logging.info('Currently {} commits behind. Automatic install disabled'.format(core.UPDATE_STATUS['behind_count']))
        return data


class ImdbRssSync(object):

    @staticmethod
    def create():
        interval = core.CONFIG['Search']['Watchlists']['imdbfrequency'] * 60
        now = datetime.datetime.now()

        hr = now.hour
        min = now.minute + core.CONFIG['Search']['Watchlists']['imdbfrequency']

        if core.CONFIG['Search']['Watchlists']['imdbsync']:
            auto_start = True
        else:
            auto_start = False

        taskscheduler.ScheduledTask(hr, min, interval, ImdbRssSync.imdb_sync,
                                    auto_start=auto_start)
        return

    @staticmethod
    def imdb_sync():
        imdb_rss = imdb.ImdbRss()
        imdb_rss.get_rss()
        return


class PopularMoviesSync(object):

    @staticmethod
    def create():
        interval = 24 * 3600

        hr = core.CONFIG['Search']['Watchlists']['popularmovieshour']
        min = core.CONFIG['Search']['Watchlists']['popularmoviesmin']

        if core.CONFIG['Search']['Watchlists']['popularmoviessync']:
            auto_start = True
        else:
            auto_start = False

        taskscheduler.ScheduledTask(hr, min, interval, PopularMoviesSync.popularmovies_sync,
                                    auto_start=auto_start)
        return

    @staticmethod
    def popularmovies_sync():
        popular_feed = popularmovies.PopularMoviesFeed()

        popular_feed.get_feed()
        return


class TraktSync(object):

    trakt = trakt.Trakt()

    @staticmethod
    def create():
        interval = core.CONFIG['Search']['Watchlists']['traktfrequency'] * 60

        now = datetime.datetime.now()

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

        taskscheduler.ScheduledTask(hr, min, interval, TraktSync.trakt.trakt_sync,
                                    auto_start=auto_start)
        return

import datetime
import logging

import cherrypy
import core
from core.notification import Notification

from core import searcher, version
from core.rss import imdb, popularmovies
from core.cp_plugins import taskscheduler
from core import trakt

logging = logging.getLogger(__name__)


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

    def __init__(self):
        # create scheduler plugin
        self.plugin = taskscheduler.SchedulerPlugin(cherrypy.engine)


# create classes for each scheduled task
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
        delay = task_search.task.delay
        now = datetime.datetime.today().replace(second=0, microsecond=0)
        core.NEXT_SEARCH = now + datetime.timedelta(0, delay)


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

        Returns dict from core.version.Version.manager.update_check():
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        ver = version.Version()

        data = ver.manager.update_check()
        # if data['status'] == 'current', nothing to do.
        if data['status'] == 'error':
            notif = {'type': 'warning',
                     'closeButton': 'true',
                     'title': 'Error Checking for Updates',
                     'body': data['error'],
                     'params': '{closeButton: true, timeOut: 0, extendedTimeOut: 0}'
                     }
            Notification.add(notif)

        elif data['status'] == 'behind':
            if data['behind_count'] == 1:
                title = '1 Update Available'
            else:
                title = '{} Updates Available'.format(data['behind_count'])

            compare = '{}/compare/{}...{}'.format(core.GIT_URL, data['local_hash'], data['new_hash'])

            notif = {'type': 'update',
                     'title': title,
                     'body': 'Click <a href="update_now"><u>here</u></a> to update now.'
                             '<br/> Click <a href="' + compare + '"><u>here</u></a> to view changes.',
                     'params': {'timeOut': 0,
                                'closeButton': 'true',
                                'extendedTimeOut': 0,
                                'tapToDismiss': 0}
                     }

            Notification.add(notif)

        return data


class AutoUpdateInstall(object):

    @staticmethod
    def create():
        interval = 24 * 3600

        hr = core.CONFIG['Server']['installupdatehr']
        min = core.CONFIG['Server']['installupdatemin']

        if core.CONFIG['Server']['installupdates']:
            auto_start = True
        else:
            auto_start = False

        taskscheduler.ScheduledTask(hr, min, interval, AutoUpdateInstall.update_install,
                                    auto_start=auto_start)
        return

    @staticmethod
    def update_install():
        ver = version.Version()

        if not core.UPDATE_STATUS or core.UPDATE_STATUS['status'] != 'behind':
            return

        logging.info('Running automatic updater.')

        logging.info('Currently {} commits behind. Updating to {}.'.format(
                     core.UPDATE_STATUS['behind_count'], core.UPDATE_STATUS['new_hash']))

        core.UPDATING = True

        logging.info('Executing update.')
        update = ver.manager.execute_update()
        core.UPDATING = False

        if not update:
            logging.error('Update failed.')

        logging.info('Update successful, restarting.')
        cherrypy.engine.restart()
        return


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
        logging.info('Running automatic IMDB rss sync.')
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
        logging.info('Running automatic popular movies sync.')

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

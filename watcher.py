import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates'))

MIN_PYTHON = (3, 0, 0)
if sys.version_info < MIN_PYTHON:
    print('Python {} or newer required.'.format(MIN_PYTHON))
    sys.exit(1)

import core
core.PROG_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(core.PROG_PATH)

import argparse
import locale
import logging
import webbrowser

import cherrypy
from cherrypy.process.plugins import Daemonizer, PIDFile
from core import api, config, postprocessing, scheduler, sqldb
from core.app import App
from core.log import log

if os.name == 'nt':
    from core.cp_plugins import systray

if __name__ == '__main__':

    # have to set locale for date parsing
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except Exception as e:
        try:
            # for windows
            locale.setlocale(locale.LC_ALL, 'English_United States.1252')
        except Exception as e:
            logging.warning('Unable to set locale. Date parsing may not work correctly.')
            print('Unable to set locale. Date parsing may not work correctly.')

    # parse user-passed arguments
    parser = argparse.ArgumentParser(description="Watcher Server App")
    parser.add_argument('-d', '--daemon', help='Run the server as a daemon.',
                        action='store_true')
    parser.add_argument('-a', '--address', help='Network address to bind to.')
    parser.add_argument('-p', '--port', help='Port to bind to.', type=int)
    parser.add_argument('-b', '--browser', help='Open browser on launch.',
                        action='store_true')
    parser.add_argument('-c', '--conf', help='Location of config file.',
                        type=str)
    parser.add_argument('-l', '--log',
                        help='Directory in which to create log files.', type=str)
    parser.add_argument('--db',
                        help='Absolute path to database file.', type=str)
    parser.add_argument('--plugins',
                        help='Directory in which plugins are stored.', type=str)
    parser.add_argument('--pid',
                        help='Directory in which to store pid file.', type=str)
    passed_args = parser.parse_args()

    if passed_args.plugins:
        core.PLUGIN_DIR = passed_args.plugins

    if passed_args.pid:
        PIDFile(cherrypy.engine, passed_args.pid).subscribe()

    # Set up conf file
    if passed_args.conf:
        core.CONF_FILE = passed_args.conf
    if passed_args.log:
        core.LOG_DIR = passed_args.log

    # set up config file on first launch
    conf = config.Config()
    if not os.path.isfile(core.CONF_FILE):
        print('Config file not found. Creating new basic config {}. Please review settings.'.format(core.CONF_FILE))
        conf.new_config()
    else:
        print('Config file found, merging any new options.')
        conf.merge_new_options()
    conf.stash()

    # Set up logging
    if passed_args.log:
        core.LOG_DIR = passed_args.log
    log.start(core.LOG_DIR)
    logging = logging.getLogger(__name__)
    cherrypy.log.error_log.propagate = True
    cherrypy.log.access_log.propagate = False

    # Set up server
    if passed_args.address:
        core.SERVER_ADDRESS = passed_args.address
    else:
        core.SERVER_ADDRESS = str(core.CONFIG['Server']['serverhost'])
    if passed_args.port:
        core.SERVER_PORT = passed_args.port
    else:
        core.SERVER_PORT = core.CONFIG['Server']['serverport']

    # set up db on first launch, check for updates afterward
    if passed_args.db:
        core.DB_FILE = passed_args.db
    else:
        core.DB_FILE = os.path.join(core.PROG_PATH, core.DB_FILE)
    sql = sqldb.SQL()
    if not os.path.isfile(core.DB_FILE):
        logging.info(u'SQL DB not found. Creating.')
        sql = sqldb.SQL()
        sql.create_database()
    else:
        logging.info(u'SQL DB found.')
        print('Database found.')
        sql.update_tables()
    del sql

    # mount and configure applications
    if core.CONFIG['Server']['customwebroot']:
        core.URL_BASE = core.CONFIG['Server']['customwebrootpath']

    root = cherrypy.tree.mount(App(),
                               u'{}/'.format(core.URL_BASE),
                               'core/conf_app.ini'
                               )
    cherrypy.tree.mount(api.API(),
                        u'{}/api'.format(core.URL_BASE),
                        'core/conf_api.ini'
                        )

    cherrypy.tree.mount(postprocessing.Postprocessing(),
                        u'{}/postprocessing'.format(core.URL_BASE),
                        'core/conf_postprocessing.ini'
                        )

    cherrypy.tree.mount(App.auth,
                        u'{}/auth'.format(core.URL_BASE),
                        'core/conf_auth.ini'
                        )

    # if everything goes well so far, open the browser
    if passed_args.browser or core.CONFIG['Server']['launchbrowser']:
        webbrowser.open(u"http://{}:{}{}".format(
            core.SERVER_ADDRESS, core.SERVER_PORT, core.URL_BASE))
        logging.info(u'Launching web browser.')

    # daemonize in *nix if desired
    if passed_args.daemon and os.name == 'posix':
        Daemonizer(cherrypy.engine).subscribe()

    os.chdir(core.PROG_PATH)  # have to do this for the daemon

    # start engine
    cherrypy.config.update('core/conf_global.ini')
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()

    # Create plugin instances and subscribe
    scheduler_plugin = scheduler.Scheduler()
    scheduler.AutoSearch.create()
    scheduler.AutoUpdateCheck.create()
    scheduler.AutoUpdateInstall.create()
    scheduler.ImdbRssSync.create()
    scheduler.PopularMoviesSync.create()
    scheduler.TraktSync.create()
    scheduler_plugin.plugin.subscribe()

    # If windows os and daemon selected, start systray
    if passed_args.daemon and os.name == 'nt':
        systrayplugin = systray.SysTrayPlugin(cherrypy.engine)
        systrayplugin.subscribe()
        systrayplugin.start()

    # finish by blocking
    cherrypy.engine.block()

# pylama:ignore=E402

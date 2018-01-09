import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))

MIN_PYTHON = (3, 0, 0)
if sys.version_info < MIN_PYTHON:
    print('Python {} or newer required.'.format('.'.join(MIN_PYTHON)))
    sys.exit(1)

import core         # noqa
core.PROG_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(core.PROG_PATH)
core.SCRIPT_PATH = os.path.join(core.PROG_PATH, os.path.basename(__file__))
if os.name == 'nt':
    core.PLATFORM = 'windows'
    from core.cp_plugins import systray
else:
    core.PLATFORM = '*nix'

import argparse     # noqa
import locale       # noqa
import logging      # noqa
import webbrowser   # noqa
import shutil       # noqa

import cherrypy     # noqa
from cherrypy.process.plugins import Daemonizer, PIDFile    # noqa

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
            print('\033[33m Unable to set locale. Date parsing may not work correctly.\033[0m')

    # parse user-passed arguments
    parser = argparse.ArgumentParser(description='Watcher Server App')
    parser.add_argument('-d', '--daemon', help='Run the server as a daemon.', action='store_true')
    parser.add_argument('-a', '--address', help='Network address to bind to.')
    parser.add_argument('-p', '--port', help='Port to bind to.', type=int)
    parser.add_argument('-b', '--browser', help='Open browser on launch.', action='store_true')
    parser.add_argument('-c', '--conf', help='Location of config file.', type=str)
    parser.add_argument('--userdata', help='Userdata dir containing database, config, etc.', type=str)
    parser.add_argument('-l', '--log', help='Directory in which to create log files.', type=str)
    parser.add_argument('--db', help='Absolute path to database file.', type=str)
    parser.add_argument('--plugins', help='Directory in which plugins are stored.', type=str)
    parser.add_argument('--pid', help='Directory in which to store pid file.', type=str)
    parser.add_argument('--debug', help='Start in Debug mode.', action='store_true')
    passed_args = parser.parse_args()

    if passed_args.userdata:
        core.USERDATA = passed_args.userdata
        core.CONF_FILE = os.path.join(passed_args.userdata, 'config.cfg')
        core.DB_FILE = os.path.join(passed_args.userdata, 'watcher.sqlite')
    if passed_args.db:
        core.DB_FILE = passed_args.db
    else:
        core.DB_FILE = os.path.join(core.PROG_PATH, core.DB_FILE)
    if passed_args.conf:
        core.CONF_FILE = passed_args.conf
    else:
        core.CONF_FILE = os.path.join(core.PROG_PATH, core.CONF_FILE)
    if passed_args.log:
        core.LOG_DIR = passed_args.log
    if passed_args.plugins:
        core.PLUGIN_DIR = passed_args.plugins

    # set up db connection
    from core import sqldb, library
    core.sql = sqldb.SQL()
    core.sql.update_database()
    core.manage = library.Manage()

    # set up config file on first launch
    from core import config
    conf = config.Config()
    if not os.path.isfile(core.CONF_FILE):
        print('\033[33m Config file not found. Creating new basic config {}. Please review settings. \033[0m'.format(core.CONF_FILE))
        conf.new_config()
    else:
        print('Config file found, merging any new options.')
        conf.merge_new_options()
    conf.stash()

    # Set up logging
    from core import log
    log.start(core.LOG_DIR, passed_args.debug or False)
    logging = logging.getLogger(__name__)
    cherrypy.log.error_log.propagate = True
    cherrypy.log.access_log.propagate = False

    # clean mako cache
    try:
        print('Clearing Mako cache.')
        shutil.rmtree(core.MAKO_CACHE)
    except FileNotFoundError:
        pass
    except Exception as e:
        print('\033[31m Unable to clear Mako cache. \033[0m')
        print(e)

    # Finish core application
    from core import config, scheduler, version
    from core.app import App
    core.updater = version.manager()

    # Set up server
    if passed_args.address:
        core.SERVER_ADDRESS = passed_args.address
    else:
        core.SERVER_ADDRESS = str(core.CONFIG['Server']['serverhost'])
    if passed_args.port:
        core.SERVER_PORT = passed_args.port
    else:
        core.SERVER_PORT = core.CONFIG['Server']['serverport']

    # mount and configure applications
    if core.CONFIG['Server']['customwebroot']:
        core.URL_BASE = core.CONFIG['Server']['customwebrootpath']

    root = cherrypy.tree.mount(App(), '{}/'.format(core.URL_BASE), 'core/conf_app.ini')

    # Start plugins
    if passed_args.daemon:
        if core.PLATFORM == '*nix':
            Daemonizer(cherrypy.engine).subscribe()
        elif core.PLATFORM == 'windows':
            systrayplugin = systray.SysTrayPlugin(cherrypy.engine)
            systrayplugin.subscribe()
            systrayplugin.start()

    scheduler.create_plugin()

    if passed_args.pid:
        PIDFile(cherrypy.engine, passed_args.pid).subscribe()

    # SSL certs
    if core.CONFIG['Server']['ssl_cert'] and core.CONFIG['Server']['ssl_key']:
        logging.info('SSL Certs are enabled. Server will only be accessible via https.')
        print('SSL Certs are enabled. Server will only be accessible via https.')
        ssl_conf = {'server.ssl_certificate': core.CONFIG['Server']['ssl_cert'],
                    'server.ssl_private_key': core.CONFIG['Server']['ssl_key'],
                    'tools.https_redirect.on': True
                    }
        try:
            from OpenSSL import SSL # noqa
        except ImportError as e:
            ssl_conf['server.ssl_module'] = 'builtin'
            m = '''
Using built-in SSL module. This may result in a large amount of
logged error messages even though everything is working correctly.
You may avoid this by installing the pyopenssl module.'''
            print(m)
            logging.info(m)
            pass
        cherrypy.config.update(ssl_conf)

    # Open browser
    if passed_args.browser or core.CONFIG['Server']['launchbrowser']:
        logging.info('Launching web browser.')
        a = 'localhost' if core.SERVER_ADDRESS == '0.0.0.0' else core.SERVER_ADDRESS
        webbrowser.open('http://{}:{}{}'.format(a, core.SERVER_PORT, core.URL_BASE))

    # start engine
    cherrypy.config.update('core/conf_global.ini')
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    os.chdir(core.PROG_PATH)  # have to do this for the daemon
    cherrypy.engine.block()

# pylama:ignore=E402

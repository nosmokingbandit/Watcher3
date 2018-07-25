import cherrypy
import core
from core import ajax, scheduler, plugins, localization, api
from core.auth import AuthController
from core.postprocessing import Postprocessing
import os
import json
from mako.template import Template

import sys
import time

locale_dir = os.path.join(core.PROG_PATH, 'locale')


class App(object):

    @cherrypy.expose
    def __init__(self):
        self.auth = AuthController()
        self.postprocessing = Postprocessing()
        self.api = api.API()

        if core.CONFIG['Server']['authrequired']:
            self._cp_config = {
                'auth.require': []
            }

        self.ajax = ajax.Ajax()
        localization.get()
        localization.install()

        # point server toward custom 404
        cherrypy.config.update({
            'error_page.404': self.error_page_404
        })

        # Lock down settings if required
        if core.CONFIG['Server']['adminrequired']:
            self.settings._cp_config['auth.require'] = [core.auth.is_admin]

        if core.CONFIG['Server']['checkupdates']:
            scheduler.AutoUpdateCheck.update_check(install=False)

    def https_redirect(self=None):
        ''' Cherrypy tool to redirect http:// to https://

        Use as before_handler when https is enabled for the server.

        Enable in config as {'tools.https_redirect.on': True}

        '''
        if cherrypy.request.scheme == 'http':
            raise cherrypy.HTTPRedirect(cherrypy.url().replace('http:', 'https:'), status=302)

    cherrypy.tools.https_redirect = cherrypy.Tool('before_handler', https_redirect)

    def defaults(self):
        defaults = {'head': self.head(),
                    'navbar': self.nav_bar(current=sys._getframe().f_back.f_code.co_name),
                    'url_base': core.URL_BASE
                    }
        return defaults

    # All dispatching methods from here down

    status_template = Template(filename='templates/library/status.html', module_directory=core.MAKO_CACHE)
    manage_template = Template(filename='templates/library/manage.html', module_directory=core.MAKO_CACHE)
    import_template = Template(filename='templates/library/import.html', module_directory=core.MAKO_CACHE)
    couchpotato_template = Template(filename='templates/library/import/couchpotato.html', module_directory=core.MAKO_CACHE)
    kodi_template = Template(filename='templates/library/import/kodi.html', module_directory=core.MAKO_CACHE)
    plex_template = Template(filename='templates/library/import/plex.html', module_directory=core.MAKO_CACHE)
    directory_template = Template(filename='templates/library/import/directory.html', module_directory=core.MAKO_CACHE)
    stats_template = Template(filename='templates/library/stats.html', module_directory=core.MAKO_CACHE)

    add_movie_template = Template(filename='templates/add_movie.html', module_directory=core.MAKO_CACHE)

    server_template = Template(filename='templates/settings/server.html', module_directory=core.MAKO_CACHE)
    search_template = Template(filename='templates/settings/search.html', module_directory=core.MAKO_CACHE)
    quality_template = Template(filename='templates/settings/quality.html', module_directory=core.MAKO_CACHE)
    indexers_template = Template(filename='templates/settings/indexers.html', module_directory=core.MAKO_CACHE)
    downloader_template = Template(filename='templates/settings/downloader.html', module_directory=core.MAKO_CACHE)
    postprocessing_template = Template(filename='templates/settings/postprocessing.html', module_directory=core.MAKO_CACHE)
    plugins_template = Template(filename='templates/settings/plugins.html', module_directory=core.MAKO_CACHE)
    logs_template = Template(filename='templates/settings/logs.html', module_directory=core.MAKO_CACHE)
    system_template = Template(filename='templates/settings/system.html', module_directory=core.MAKO_CACHE)

    shutdown_template = Template(filename='templates/system/shutdown.html', module_directory=core.MAKO_CACHE)
    restart_template = Template(filename='templates/system/restart.html', module_directory=core.MAKO_CACHE)
    update_template = Template(filename='templates/system/update.html', module_directory=core.MAKO_CACHE)

    fourohfour_template = Template(filename='templates/404.html', module_directory=core.MAKO_CACHE)
    head_template = Template(filename='templates/head.html', module_directory=core.MAKO_CACHE)
    navbar_template = Template(filename='templates/navbar.html', module_directory=core.MAKO_CACHE)

    @cherrypy.expose
    def default(self):
        return self.library('status')

    @cherrypy.expose
    def _test(self):
        return 'This is not the page you are looking for.'

    @cherrypy.expose
    def library(self, *path):
        page = path[0] if len(path) > 0 else 'status'

        if page == 'status':

            mc, fc = core.sql.get_library_count()

            return App.status_template.render(profiles=core.CONFIG['Quality']['Profiles'].keys(), movie_count=mc, finished_count=fc, **self.defaults())
        elif page == 'manage':
            movies = core.sql.get_user_movies()
            return App.manage_template.render(movies=movies, profiles=core.CONFIG['Quality']['Profiles'].keys(), **self.defaults())
        elif page == 'import':
            subpage = path[1] if len(path) > 1 else None

            if not subpage:
                return App.import_template.render(**self.defaults())
            elif subpage == 'couchpotato':
                return App.couchpotato_template.render(sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys(), **self.defaults())
            elif subpage == 'kodi':
                return App.kodi_template.render(sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys(), **self.defaults())
            elif subpage == 'plex':
                return App.plex_template.render(sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys(), **self.defaults())
            elif subpage == 'directory':
                try:
                    start_dir = os.path.expanduser('~')
                    file_list = [i for i in os.listdir(start_dir) if os.path.isdir(os.path.join(start_dir, i)) and not i.startswith('.')]
                except Exception as e:
                    start_dir = core.PROG_PATH
                    file_list = [i for i in os.listdir(start_dir) if os.path.isdir(os.path.join(start_dir, i)) and not i.startswith('.')]
                file_list.append('..')
                return App.directory_template.render(sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys(), current_dir=start_dir, file_list=file_list, **self.defaults())
            else:
                return self.error_page_404()
        elif page == 'stats':
            App.stats_template = Template(filename='templates/library/stats.html', module_directory=core.MAKO_CACHE)

            return App.stats_template.render(**self.defaults())
        else:
            return self.error_page_404()

    @cherrypy.expose
    def add_movie(self):
        return App.add_movie_template.render(profiles=[(k, v.get('default', False)) for k, v in core.CONFIG['Quality']['Profiles'].items()], **self.defaults())

    @cherrypy.expose
    def settings(self, *path):
        page = path[0] if len(path) > 0 else 'server'

        if page == 'server':
            themes = [i[:-4] for i in os.listdir('static/css/themes/') if i.endswith('.css') and os.path.isfile(os.path.join(core.PROG_PATH, 'static/css/themes', i))]
            return App.server_template.render(config=core.CONFIG['Server'], themes=themes, version=core.CURRENT_HASH or '', languages=core.LANGUAGES.keys(), **self.defaults())
        elif page == 'search':
            return App.search_template.render(config=core.CONFIG['Search'], **self.defaults())
        elif page == 'quality':
            return App.quality_template.render(config=core.CONFIG['Quality'], sources=core.SOURCES, **self.defaults())
        elif page == 'indexers':
            return App.indexers_template.render(config=core.CONFIG['Indexers'], **self.defaults())
        elif page == 'downloader':
            return App.downloader_template.render(config=core.CONFIG['Downloader'], **self.defaults())
        elif page == 'postprocessing':
            return App.postprocessing_template.render(config=core.CONFIG['Postprocessing'], os=core.PLATFORM, **self.defaults())
        elif page == 'plugins':
            plugs = plugins.list_plugins()
            return App.plugins_template.render(config=core.CONFIG['Plugins'], plugins=plugs, **self.defaults())
        elif page == 'logs':
            logdir = os.path.join(core.PROG_PATH, core.LOG_DIR)
            logfiles = [i for i in os.listdir(logdir) if os.path.isfile(os.path.join(logdir, i))]
            return App.logs_template.render(logdir=logdir, logfiles=logfiles, **self.defaults())
        elif page == 'download_log':
            if len(path) > 1:
                l = os.path.join(os.path.abspath(core.LOG_DIR), path[1])
                return cherrypy.lib.static.serve_file(l, 'application/x-download', 'attachment')
            else:
                raise cherrypy.HTTPError(400)
        elif page == 'system':
            tasks = {}
            for name, obj in core.scheduler_plugin.task_list.items():
                tasks[name] = {'name': name,
                               'interval': obj.interval,
                               'last_execution': obj.last_execution,
                               'enabled': obj.timer.is_alive() if obj.timer else False}

            system = {'database': {'file': core.DB_FILE,
                                   'size': os.path.getsize(core.DB_FILE) / 1024
                                   },
                      'config': {'file': core.CONF_FILE},
                      'system': {'path': core.PROG_PATH,
                                 'arguments': sys.argv,
                                 'version': sys.version[:5]}
                      }
            t = int(time.time())
            dt = time.strftime('%a, %B %d, %Y %H:%M:%S %z', time.localtime(t))

            return App.system_template.render(config=core.CONFIG['System'], tasks=json.dumps(tasks), system=system, server_time=[dt, t], **self.defaults())
        else:
            return self.error_page_404()
    settings._cp_config = {}

    @cherrypy.expose
    def system(self, *path, **kwargs):
        if len(path) == 0:
            return self.error_page_404()

        page = path[0]

        if page == 'shutdown':
            return App.shutdown_template.render(**self.defaults())
        if page == 'restart':
            return App.restart_template.render(**self.defaults())
        if page == 'update':
            return App.update_template.render(updating=core.UPDATING, **self.defaults())

    @cherrypy.expose
    def error_page_404(self, *args, **kwargs):
        return App.fourohfour_template.render(**self.defaults())

    def head(self):
        return App.head_template.render(url_base=core.URL_BASE, uitheme=core.CONFIG['Server']['uitheme'], notifications=json.dumps([i for i in core.NOTIFICATIONS if i is not None]), language=core.LANGUAGE)

    def nav_bar(self, current=None):
        username = cherrypy.session.get(core.SESSION_KEY)
        return App.navbar_template.render(url_base=core.URL_BASE, current=current, username=username)

import cherrypy
import core
from core import ajax, scheduler, plugins
from core.auth import AuthController
import os
import json
from mako.template import Template


class App(object):

    auth = AuthController()

    @cherrypy.expose
    def __init__(self):
        if core.CONFIG['Server']['authrequired']:
            self._cp_config = {
                'auth.require': []
            }

        self.ajax = ajax.Ajax()

        # point server toward custom 404
        cherrypy.config.update({
            'error_page.404': self.error_page_404
        })

        if core.CONFIG['Server']['checkupdates']:
            scheduler.AutoUpdateCheck.update_check()

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
        h = ''
        active_tasks = [k for k, v in core.scheduler_plugin.task_list.items() if v.running]

        return ', '.join(active_tasks)

    @cherrypy.expose
    def library(self, *path):
        page = path[0] if len(path) > 0 else 'status'

        if page == 'status':
            movie_count = core.sql.get_library_count()
            return App.status_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), profiles=core.CONFIG['Quality']['Profiles'].keys(), movie_count=movie_count)
        elif page == 'manage':
            movies = core.sql.get_user_movies()
            return App.manage_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), movies=movies, profiles=core.CONFIG['Quality']['Profiles'].keys())
        elif page == 'import':
            subpage = path[1] if len(path) > 1 else None

            if not subpage:
                return App.import_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'))
            elif subpage == "couchpotato":
                return App.couchpotato_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys())
            elif subpage == "kodi":
                return App.kodi_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys())
            elif subpage == "plex":
                return App.plex_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys())
            elif subpage == "directory":
                try:
                    start_dir = os.path.expanduser("~")
                    file_list = [i for i in os.listdir(start_dir) if os.path.isdir(os.path.join(start_dir, i)) and not i.startswith('.')]
                except PermissionError as e:
                    start_dir = core.PROG_PATH
                    file_list = [i for i in os.listdir(start_dir) if os.path.isdir(os.path.join(start_dir, i)) and not i.startswith('.')]
                file_list.append('..')
                return App.directory_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'), sources=core.SOURCES, profiles=core.CONFIG['Quality']['Profiles'].keys(), current_dir=start_dir, file_list=file_list)
            else:
                return self.error_page_404()
        elif page == 'stats':
            return App.stats_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='status'))
        else:
            return self.error_page_404()

    @cherrypy.expose
    def add_movie(self):
        return App.add_movie_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='add_movie'), profiles=[i for i in core.CONFIG['Quality']['Profiles'] if i != 'Default'])

    @cherrypy.expose
    def settings(self, *path):
        page = path[0] if len(path) > 0 else 'server'

        if page == 'server':
            themes = [i[:-4] for i in os.listdir('static/css/themes/') if i.endswith(".css") and os.path.isfile(os.path.join(core.PROG_PATH, 'static/css/themes', i))]
            return App.server_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Server'], themes=themes, version=core.CURRENT_HASH or '')
        elif page == 'search':
            return App.search_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Search'])
        elif page == 'quality':
            return App.quality_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Quality'], sources=core.SOURCES)
        elif page == 'indexers':
            return App.indexers_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Indexers'])
        elif page == 'downloader':
            return App.downloader_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Downloader'])
        elif page == 'postprocessing':
            return App.postprocessing_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Postprocessing'], os=core.PLATFORM)
        elif page == 'plugins':
            plugs = plugins.list_plugins()
            return App.plugins_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), config=core.CONFIG['Plugins'], plugins=plugs)
        elif page == 'logs':
            logdir = os.path.join(core.PROG_PATH, core.LOG_DIR)
            logfiles = [i for i in os.listdir(logdir) if os.path.isfile(os.path.join(logdir, i))]
            return App.logs_template.render(url_base=core.URL_BASE, head=self.head(), navbar=self.nav_bar(current='settings'), logdir=logdir, logfiles=logfiles)
        else:
            return self.error_page_404()

    @cherrypy.expose
    def system(self, *path):
        if len(path) == 0:
            return self.error_page_404()

        page = path[0]

        if page == 'shutdown':
            return App.shutdown_template.render(url_base=core.URL_BASE, head=self.head())
        if page == 'restart':
            return App.restart_template.render(url_base=core.URL_BASE, head=self.head())
        if page == 'update':
            return App.update_template.render(url_base=core.URL_BASE, head=self.head(), updating=core.UPDATING)

    @cherrypy.expose
    def error_page_404(self, *args, **kwargs):
        return App.fourohfour_template.render(url_base=core.URL_BASE, head=self.head())

    def head(self):
        return App.head_template.render(url_base=core.URL_BASE, uitheme=core.CONFIG['Server']['uitheme'], notifications=json.dumps([i for i in core.NOTIFICATIONS if i is not None]))

    def nav_bar(self, current=None):
        show_logout = True if cherrypy.session.get(core.SESSION_KEY) else False
        return App.navbar_template.render(url_base=core.URL_BASE, current=current, show_logout=show_logout)

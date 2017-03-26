import cherrypy
import core
from core import ajax, scheduler
from core.auth import AuthController
from templates import (add_movie, fourohfour, import_library, restart, settings,
                       shutdown, status, update)


class App(object):

    auth = AuthController()

    @cherrypy.expose
    def __init__(self):
        if core.CONFIG['Server']['authrequired']:
            self._cp_config = {
                'auth.require': []
            }

        self.ajax = ajax.Ajax()
        self.add_movie = add_movie.AddMovie()
        self.status = status.Status()
        self.settings = settings.Settings()
        self.restart = restart.Restart()
        self.shutdown = shutdown.Shutdown()
        self.update = update.Update()
        self.import_library = import_library.ImportLibrary()

        # point server toward custom 404
        cherrypy.config.update({
            'error_page.404': self.error_page_404
        })

        if core.CONFIG['Server']['checkupdates']:
            scheduler.AutoUpdateCheck.update_check()

        return

    @cherrypy.expose
    def default(self):
        raise cherrypy.InternalRedirect('/status/')

    @cherrypy.expose
    def error_page_404(self, *args, **kwargs):
        return fourohfour.FourOhFour.default()

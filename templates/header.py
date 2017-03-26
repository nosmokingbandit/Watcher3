import core
from dominate.tags import *


class Header():
    ''' Header for pages with NavBar.
    '''

    @staticmethod
    def insert_header(current):

        with div(id='header'):
            with div(id='header_container'):
                img(src=core.URL_BASE + '/static/images/logo.png', alt='')
                with ul(id='nav'):
                    if current == 'settings':
                        cls = 'settings current'
                    else:
                        cls = 'settings'
                    with li(u'Settings', cls=cls):
                            with ul(cls='settings_menu'):
                                with a(href=core.URL_BASE + '/settings/server/'):
                                    with li():
                                        i(cls='fa fa-server')
                                        span(u'Server')
                                with a(href=core.URL_BASE + '/settings/search/'):
                                    with li():
                                        i(cls='fa fa-search')
                                        span(u'Search')
                                with a(href=core.URL_BASE + '/settings/quality/'):
                                    with li():
                                        i(cls='fa fa-filter')
                                        span(u'Quality')
                                with a(href=core.URL_BASE + '/settings/providers/'):
                                    with li():
                                        i(cls='fa fa-plug')
                                        span(u'Providers')
                                with a(href=core.URL_BASE + '/settings/downloader/'):
                                    with li():
                                        i(cls='fa fa-download')
                                        span(u'Downloader')
                                with a(href=core.URL_BASE + '/settings/postprocessing/'):
                                    with li():
                                        i(cls='fa fa-film')
                                        span(u'Post Processing')
                                with a(href=core.URL_BASE + '/settings/plugins/'):
                                    with li():
                                        i(cls='fa fa-puzzle-piece')
                                        span(u'Plugins')
                                with a(href=core.URL_BASE + '/settings/logs/'):
                                    with li():
                                        i(cls='fa fa-file-text')
                                        span(u'Logs')
                                with a(href=core.URL_BASE + '/settings/about/'):
                                    with li():
                                        i(cls='fa fa-info-circle')
                                        span(u'About')

                    with a(href=core.URL_BASE + '/add_movie/'):
                        if current == 'add_movie':
                            cls = 'add_movie current'
                        else:
                            cls = 'add_movie'
                        li(u'Add Movie', cls=cls)

                    with a(href=core.URL_BASE + '/status/'):
                        if current == 'status':
                            cls = 'status current'
                        else:
                            cls = 'status'
                        li(u'Status', cls=cls)

# pylama:ignore=W0401

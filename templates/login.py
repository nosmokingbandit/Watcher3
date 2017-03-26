import dominate
import core
from cherrypy import expose
from dominate.tags import *


class Login(object):

    @expose
    def default(self, username=None, from_page=''):
        if username is None:
            username = ''

        doc = dominate.document(title='Watcher')

        with doc.head:
            meta(name='robots', content='noindex, nofollow')
            meta(name='url_base', content=core.URL_BASE)

            link(rel='stylesheet', href=core.URL_BASE + '/auth/static/css/style.css?v=03.15')
            link(rel='stylesheet', href=core.URL_BASE + '/auth/static/css/{}style.css?v=03.15'.format(core.CONFIG['Server']['theme']))
            link(rel='stylesheet', href=core.URL_BASE + '/auth/static/css/login.css?v=02.22')
            link(rel='stylesheet', href=core.URL_BASE + '/auth/static/css/{}login.css?v=02.22'.format(core.CONFIG['Server']['theme']))
            link(rel='stylesheet', href='//fonts.googleapis.com/css?family=Raleway')
            link(rel='stylesheet', href=core.URL_BASE + '/auth/static/font-awesome/css/font-awesome.css')
            script(type='text/javascript', src='https://ajax.googleapis.com/ajax/libs/jquery/3.1.0/jquery.min.js')
            script(type='text/javascript', src='https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.0/jquery-ui.min.js')
            script(type='text/javascript', src=core.URL_BASE + '/auth/static/js/login/main.js?v=02.02b')

        with doc:
            with div(id='content'):
                img(src=core.URL_BASE + '/auth/static/images/logo.png', id='logo')
                br()
                with div(id='login_form'):
                    input(type='text', id='username', placeholder='Username', value=username)
                    br()
                    input(type='password', id='password', placeholder='Password')
                    br()
                    i(cls='fa fa-sign-in', id='send_login')

        return doc.render()

# pylama:ignore=W0401

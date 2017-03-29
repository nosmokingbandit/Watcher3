import core
import dominate
from cherrypy import expose
from dominate.tags import *
from head import Head


class FourOhFour():

    @staticmethod
    @expose
    def default():

        doc = dominate.document(title='Watcher')

        with doc.head:
            meta(name='enable_notifs', content='false')
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/fourohfour.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}fourohfour.css?v=03.28'.format(core.CONFIG['Server']['theme']))

        with doc:
            with div(id='content'):
                with span(cls='msg'):
                    span('404')
                    br()
                    span('Page Not Found')

        return doc.render()

# pylama:ignore=W0401

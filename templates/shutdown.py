import core
import dominate
from cherrypy import expose
from dominate.tags import *
from head import Head


class Shutdown():

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')

        with doc.head:
            meta(name='enable_notifs', content='false')
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/shutdown.css?v=02.22')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}shutdown.css?v=02.22'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/shutdown/main.js?v=02.22')

        with doc:
            with div(id='content'):
                div(id='thinker')
                span(u'Shutting Down', cls='msg')

        return doc.render()

# pylama:ignore=W0401

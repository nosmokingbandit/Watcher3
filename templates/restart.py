import core
import dominate
from cherrypy import expose
from dominate.tags import *
from head import Head


class Restart():

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')

        with doc.head:
            meta(name='enable_notifs', content='false')
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/restart\.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}restart\.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/restart/main\.js?v=03.28')

        with doc:
            with div(id='content'):
                div(id='thinker')
                span(u'Restarting', cls='msg')
                with span(u'Timeout Exceeded.', cls='error'):
                    p(u'Watcher is taking too long to restart, please check your logs and restart manually.')

        return doc.render()

# pylama:ignore=W0401

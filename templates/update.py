import core
import dominate
from cherrypy import expose
from dominate.tags import *
from head import Head


class Update():

    @expose
    def default(self):
        if core.UPDATING:
            updating = 'true'
        else:
            updating = 'false'

        doc = dominate.document(title='Watcher')

        with doc.head:
            meta(name='enable_notifs', content='false')
            meta(name='updating', content=updating)
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/update.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}update.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/update/main.js?v=03.28')

        with doc:
            with div(id='content'):
                div(id='thinker')
                span(u'Updating', cls='msg')

        return doc.render()

# pylama:ignore=W0401

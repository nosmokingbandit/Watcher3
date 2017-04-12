import core
import dominate
from cherrypy import expose
from core import sqldb
from dominate.tags import *
from header import Header
from head import Head
import json


class Manage(object):

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/manage.css?v=04.12')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}manage.css?v=04.12'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/manage/main.js?v=04.12')

        with doc:
            Header.insert_header(current="status")
            with div(id='content'):
                self.movie_list()

                with div(id='select_actions'):
                    button('Select All', id='select_all')
                    button('De-select All', id='de_select_all')
                    button('Invert Selection', id='invert_selection')
                with table(id='actions'):
                    with tr():
                        with td():
                            with button(id='metadata_update'):
                                i(cls='fa fa-refresh')
                                span('Refresh Metadata')
                        td('Re-download metadata and poster')
                    with tr():
                        with td():
                            with button(id='quality'):
                                i(cls='fa fa-filter')
                                span('Change Quality')
                        with td('Change Quality profile to: '):
                            with select(id='select_quality'):
                                for qual in core.CONFIG['Quality']['Profiles']:
                                    if qual == 'Default':
                                        option(qual, value=qual, selected='selected')
                                    else:
                                        option(qual, value=qual)
                    with tr():
                        with td():
                            with button(id='remove'):
                                i(cls='fa fa-trash')
                                span('Remove Movies')
                        td('Remove movie from library')
                    with tr():
                        with td():
                            with button(id='reset'):
                                i(cls='fa fa-rotate-left')
                                span('Reset Movies')
                        td('Remove status settings and search results')

            div(id='overlay')

        return doc.render()

    @staticmethod
    def movie_list():
        movies = sqldb.SQL().get_user_movies()

        if movies == []:
            return None
        elif not movies:
            html = 'Error retrieving list of user\'s movies. Check logs for more information'
            return str(html)

        movie_table = table(id='movie_table')
        with movie_table:
            with tr():
                th('')
                th('Poster')
                th('Title')
                th('Year')
                th('IMDB')
                th('Status')
                th('Quality')
            for data in movies:
                poster_path = core.URL_BASE + '/static/images/posters/{}.jpg'.format(data['imdbid'])
                with tr():
                    with td():
                        i(cls='fa fa-square-o checkbox', value='False')
                        span(json.dumps(data), cls='hidden data')
                    with td():
                        img(src=poster_path)
                    td(data['title'])
                    td(data['year'])
                    td(data['imdbid'], cls='imdbid')
                    with td():
                        status = data['status']
                        if status == 'Wanted':
                            span('Wanted', cls='status wanted')
                            span('1', cls='status_sort hidden')
                        elif status == 'Found':
                            span('Found', cls='status found')
                            span('2', cls='status_sort hidden')
                        elif status == 'Snatched':
                            span('Snatched', cls='status snatched')
                            span('3', cls='status_sort hidden')
                        elif status in ['Finished', 'Disabled']:
                            span('Finished', cls='status finished')
                            span('4', cls='status_sort hidden')
                        else:
                            span('Status Unknown', cls='status wanted')
                    td(data['quality'])

        return str(movie_table)

# pylama:ignore=W0401

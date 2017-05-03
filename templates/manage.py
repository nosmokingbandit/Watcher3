import core
import dominate
from cherrypy import expose
from core import sqldb, library
from dominate.tags import *
from header import Header
from head import Head
import json


class Manage(object):

    def __init__(self):
        self.library = library.Status()
        self.sql = sqldb.SQL()

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/manage.css?v=05.03')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}manage.css?v=05.03'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/manage/main.js?v=04.27')
            script(type='text/javascript', src=core.URL_BASE + '/static/js/morris/morris.js')
            script(type='text/javascript', src=core.URL_BASE + '/static/js/raphael/raphael.js')

        with doc:
            Header.insert_header(current="status")
            self.movies = self.sql.get_user_movies()

            with div(id='content'):
                with ul(id='subnav'):
                    with a(href='#database', page='_database'):
                        li('Database')
                    with a(href='#stats', page='_stats'):
                        li('Stats')

                with div(id='_database', cls='hidden'):
                    with div(id='select_actions'):
                        button('Select All', id='select_all')
                        button('De-select All', id='de_select_all')
                        button('Invert Selection', id='invert_selection')
                    self.movie_list()

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

                with div(id='_stats'):
                    with div(id='stats_container', cls='hidden'):
                        with div(cls='chart_box'):
                            with span():
                                b('Movie Count: ')
                                span(len(self.movies))
                                br()
                                b('Estimated Library Size: ')
                                span(self.library.estimate_size())
                        with div(id='chart_status', cls='chart_box'):
                            h1('Status')
                            div(cls='chart')
                        with div(id='chart_qualities', cls='chart_box'):
                            h1('Quality Profiles')
                            div(cls='chart')
                        with div(id='chart_years', cls='chart_box'):
                            h2('Movies by Year')
                            div(cls='chart')
                        with div(id='chart_added', cls='chart_box'):
                            h2('Add Frequency')
                            div(cls='chart')

                    with div(cls='chart_box'):
                        with span(id='generate_stats'):
                            i(cls='fa fa-bar-chart')
                            dominate.util.text(' Generate Stats')
                        span('Generating stats for a large library may take some time', cls='tip')

            div(id='overlay')

        return doc.render()

    def movie_list(self):
        if self.movies == []:
            return None
        elif not self.movies:
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
            for movie in self.movies:
                poster_path = core.URL_BASE + '/static/images/posters/{}.jpg'.format(movie['imdbid'])
                with tr():
                    with td():
                        i(cls='fa fa-square-o checkbox', value='False')
                        span(json.dumps(movie, sort_keys=True), cls='hidden data')
                    with td():
                        img(src=poster_path)
                    td(movie['title'])
                    td(movie['year'])
                    td(movie['imdbid'], cls='imdbid')
                    with td():
                        status = movie['status']
                        if status == 'Waiting':
                            span('Waiting', cls='status waiting')
                            span('0', cls='status_sort hidden')
                        elif status == 'Wanted':
                            span('Wanted', cls='status wanted')
                            span('1', cls='status_sort hidden')
                        elif status == 'Found':
                            span('Found', cls='status found')
                            span('2', cls='status_sort hidden')
                        elif status == 'Snatched':
                            span('Snatched', cls='status snatched')
                            span('3', cls='status_sort hidden')
                        elif status in ('Finished', 'Disabled'):
                            span('Finished', cls='status finished')
                            span('4', cls='status_sort hidden')
                        else:
                            span('Status Unknown', cls='status wanted')
                    td(movie['quality'])

        return str(movie_table)

# pylama:ignore=W0401

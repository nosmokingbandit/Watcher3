import core
import dominate
from cherrypy import expose
from core import sqldb
from dominate.tags import *
from header import Header
from head import Head


class Status():

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/status.css?v=04.23')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}status.css?v=04.23'.format(core.CONFIG['Server']['theme']))
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/movie_status_popup.css?v=04.23')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}movie_status_popup.css?v=04.23'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/status/main.js?v=03.28')

        with doc:
            Header.insert_header(current="status")
            with div(id='content'):
                with div(id='view_config'):
                    span('Display: ')
                    with select(id='list_style'):
                        options = ['Posters', 'List', 'Compact']
                        for opt in options:
                            option(opt, value=opt.lower())
                    span('Order By: ')
                    with select(id='list_sort'):
                        options = ['Status', 'Title', 'Year']
                        option('Title', value='title')
                        option('Year', value='year')
                        option('Status', value='status_sort')
                with div(id='key'):
                    span(cls='waiting')
                    span('Waiting')
                    span(cls='wanted')
                    span('Wanted')
                    span(cls='found')
                    span('Found')
                    span(cls='snatched')
                    span('Snatched')
                    span(cls='finished')
                    span('Finished')
                self.movie_list()

            with div(id='manage'):
                with a(href='{}/manage'.format(core.URL_BASE)):
                    i(cls='fa fa-briefcase', id='manage')
                    span('Manage library')

            with div(id='import'):
                with a(href='{}/import_library'.format(core.URL_BASE)):
                    i(cls='fa fa-hdd-o', id='import_library')
                    span('Import existing library')

            div(id='overlay')
            div(id='status_pop_up')

        return doc.render()

    @staticmethod
    def movie_list():
        movies = sqldb.SQL().get_user_movies()

        if movies == []:
            return None
        elif not movies:
            html = 'Error retrieving list of user\'s movies. Check logs for more information'
            return str(html)

        movie_list = ul(id='movie_list')
        with movie_list:
            for data in movies:
                poster_path = core.URL_BASE + '/static/images/posters/{}.jpg'.format(data['imdbid'])
                with li(cls='movie', imdbid=data['imdbid']):
                    with div():
                        status = data['status']
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

                        img(src=poster_path, alt='Poster for {}'.format(data['imdbid']))

                        with span(cls='movie_info'):
                            span(data['title'], cls='title', title=data['title'])
                            span(data['year'], cls='year')
                            with span(cls='score'):
                                if data['score'] == 'N/A':
                                    for nostar in range(5):
                                        i(cls='fa fa-star-o')
                                else:
                                    score = int(data['score'][0])
                                    count = 0
                                    for star in range(int(score / 2)):
                                        count += 1
                                        i(cls='fa fa-star')
                                    if score % 2 == 1:
                                        count += 1
                                        i(cls='fa fa-star-half-o')
                                    for nostar in range(5 - count):
                                        i(cls='fa fa-star-o')
                            if data['rated']:
                                span(data['rated'], cls='rated')

        return str(movie_list)

# pylama:ignore=W0401

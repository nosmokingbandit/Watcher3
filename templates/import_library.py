import core
import dominate
from cherrypy import expose
from dominate.tags import *
from header import Header
from head import Head
import json
import os


class ImportLibrary():

    @expose
    def default(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/import_library.css?v=04.04')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}import_library.css?v=04.04'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/import_library/main.js?v=04.07')

        with doc:
            Header.insert_header(current=None)
            with div(id='content'):
                h1('Import Library')
                with div(id='import_sources'):
                    with div():
                        with a(href=core.URL_BASE + '/import_library/couchpotato'):
                            img(src=core.URL_BASE + '/static/images/couchpotato.png', alt='CouchPotato', cls='import_source_icon')
                            br()
                            span('CouchPotato')
                    with div():
                        with a(href=core.URL_BASE + '/import_library/kodi'):
                            img(src=core.URL_BASE + '/static/images/kodi.png', alt='Kodi', cls='import_source_icon')
                            br()
                            span('Kodi')
                    with div():
                        with a(href=core.URL_BASE + '/import_library/plex'):
                            img(src=core.URL_BASE + '/static/images/plex.png', alt='Plex', cls='import_source_icon')
                            br()
                            span('Plex')
                    with div():
                        with a(href=core.URL_BASE + '/import_library/directory'):
                            i(cls='fa fa-folder import_source_icon')
                            br()
                            span('Directory')
        return doc.render()

    @expose
    def directory(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/import_library.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}import_library.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/import_library/main.js?v=03.28')

        with doc:
            Header.insert_header(current=None)
            with div(id='content'):
                h1('Import Library')
                with div(id='scan_dir'):
                    with div(id='directory_info'):
                        span('Library directory: ')
                        input(id='directory', type='text', placeholder=' /movies', style='width:20em')
                        with div(id='browse'):
                            i(cls='fa fa-ellipsis-h')
                        br()
                        span('Minimum file size to import: ')
                        input(id='minsize', type='number', value='500')
                        span('MB.')
                        br()
                        i(cls='fa fa-check-square checkbox', id='recursive', value='True')
                        span('Scan recursively.')
                        with div():
                            with span(id='start_scan'):
                                i(cls='fa fa-binoculars', id='start_scan')
                                span('Start scan')

                    with div(id='browser', cls='hidden'):
                        div(os.getcwd(), id='current_dir')
                        with ul(id='file_list'):
                            ImportLibrary.file_list(core.PROG_PATH)
                        with div(id='browser_actions'):
                            i(id='select_dir', cls='fa fa-check-circle')
                            i(id='close_browser', cls='fa fa-times-circle')

                with div(id='wait_scanning', cls='hidden'):
                    span('Scanning library for new movies.')
                    br()
                    span('This may take several minutes.')
                    br()
                    with span(id='scan_progress'):
                        span(cls='progress_bar')
                    span(id='scan_progress_text')

                with div(id='list_files'):
                    span(json.dumps(core.RESOLUTIONS), cls='hidden', id='resolution_list')
                    with div(id='scan_success', cls='hidden'):
                        span('The following movies have been found.', cls='title')
                        br()
                        span('Review and un-check any unwanted files.')
                        with table(cls='files'):
                            with tr():
                                th('Import')
                                th('File Path')
                                th('Title')
                                th('IMDB ID')
                                th('Source')
                                th('Size')
                    with div(id='scan_missing', cls='hidden'):
                        span('The following movies are missing key data.', cls='title')
                        br()
                        span('Please fill out or correct IMDB ID and source, or uncheck to ignore.')
                        with table(cls='files'):
                            with tr():
                                th('Import')
                                th('File Path')
                                th('Title')
                                th('IMDB ID')
                                th('Source')
                                th('Size')

                    with span(id='import'):
                        i(cls='fa fa-check-circle')
                        span('Import')

                with div(id='wait_importing', cls='hidden'):
                    span('Importing selected movies.')
                    br()
                    span('This may take several minutes.')
                    br()
                    with span(id='import_progress'):
                        span(cls='progress_bar')
                    span(id='import_progress_text')

                with div(id='import_results', cls='hidden'):
                    with table(id='import_success', cls='hidden'):
                        span('Imported:')
                        with tr():
                            th('Title')
                            th('IMDB ID')
                    with table(id='import_error', cls='hidden'):
                        with tr():
                            th('File')
                            th('Error')
                    with a(id='finished', href='{}/status'.format(core.URL_BASE), cls='hidden'):
                        i(cls='fa fa-thumbs-o-up')
                        span('Cool')

            with div(id='no_new_movies', cls='hidden'):
                h3('No new movies found')
                br()
                with a(href=core.URL_BASE+'/import_library'):
                    i(cls='fa fa-arrow-circle-left')
                    span('Return')

            div(id='thinker')
        return doc.render()

    @staticmethod
    def file_list(directory):
        subdirs = [i for i in os.listdir(directory) if os.path.isdir(os.path.join(directory, i).encode('utf-8'))]

        subdirs.insert(0, '..')

        html = ''

        for i in subdirs:
            html += str(li(i))

        return str(html)

    @staticmethod
    def render_complete(successful, failed):
        with div(id='results') as div_results:

            if failed:
                span('The following movies failed to import.')
                with table(id='failed'):
                    with tr():
                        th('File Path')
                        th('Error')
                    for movie in failed:
                        with tr():
                            td(movie['filepath'])
                            td(movie['error'])
            if successful:
                span('Successfully imported the following movies.')
                with table(id='success'):
                    with tr():
                        th('Title')
                        th('IMDB ID')
                    for movie in successful:
                        with tr():
                            td('{} ({})'.format(movie['title'], movie['year']))
                            td(movie['imdbid'])

            with a(id='finished', href='{}/status'.format(core.URL_BASE)):
                i(cls='fa fa-thumbs-o-up')
                span('Cool')
        return str(div_results)

    @expose
    def kodi(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/import_library.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}import_library.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/import_library/main.js?v=03.28')

        with doc:
            Header.insert_header(current=None)
            span(json.dumps(core.RESOLUTIONS), cls='hidden', id='resolution_list')
            with div(id='content'):
                with div(id='kodi_server_info'):
                    h1('Import Kodi Library')
                    h2('Enter Kodi server information:')
                    with p():
                        with select(id='scheme'):
                            option('http://', value='http://')
                            option('https://', value='https://')
                        input(type='text', placeholder='localhost', id='kodi_address')
                        span(':')
                        input(type='number', placeholder='8080', id='kodi_port')
                    with p('Username'):
                        input(type='text', placeholder='Kodi', id='kodi_user', style='width: 18em;')
                    with p('Password'):
                        input(type='text', placeholder='password', id='kodi_pass', style='width: 18em;')

                    with div(id='start_import_kodi'):
                        i(cls='fa fa-cloud-download')
                        span('Import Library')

                with div(id='kodi_response', cls='hidden'):
                    with div(id='kodi_remote_map'):
                        h2('Remote paths')
                        p('Kodi lists file locations relative to itself. If Kodi is on a '
                          'different device than Watcher you may need to alter file paths.')
                        with p('To alter a remote path, enter the information in the following '
                               'form and click Apply. Multiple changes can be applied. Use the '
                               'same principles as described in the '):
                            a('Wiki.', href='https://github.com/nosmokingbandit/Watcher3/wiki/Remote-Mapping')
                        p('Click Reset to return all paths to their original location.')
                        br()

                        with span('Local path: '):
                            input(id='kodi_local_path', placeholder='//Movies/', type='text')
                        with span('Remote path: '):
                            input(id='kodi_remote_path', placeholder='//Movies/', type='text')

                        button('Apply', id='kodi_apply_remote')
                        button('Reset', id='kodi_reset_remote')
                    with table():
                        with tr():
                            th('Import', style='width: 1em; text-align: center;')
                            th('File')
                            th('Title')
                            th('IMDBID', style='width: 1em;')
                            th('Source', style='width: 1em;')
                    with span(id='kodi_import'):
                        i(cls='fa fa-check-circle')
                        span('Import')

                with div(id='kodi_wait_importing', cls='hidden'):
                    span('Importing selected movies.')
                    br()
                    span('This may take several minutes.')
                    br()
                    with span(id='import_progress'):
                        span(cls='progress_bar')
                    span(id='import_progress_text')

                with div(id='kodi_import_results', cls='hidden'):
                    with table(id='kodi_import_success', cls='hidden'):
                        span('Imported:')
                        with tr():
                            th('Title')
                            th('IMDB ID')
                    with table(id='kodi_import_error', cls='hidden'):
                        with tr():
                            th('File')
                            th('Error')
                    with a(id='finished', href='{}/status'.format(core.URL_BASE), cls='hidden'):
                        i(cls='fa fa-thumbs-o-up')
                        span('Cool')

            with div(id='no_new_movies', cls='hidden'):
                h3('No new movies found')
                br()
                with a(href=core.URL_BASE+'/import_library'):
                    i(cls='fa fa-arrow-circle-left')
                    span('Return')

            div(id='thinker')
        return doc.render()

    @expose
    def plex(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/import_library.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}import_library.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/import_library/main.js?v=03.28')

        with doc:
            Header.insert_header(current=None)
            span(json.dumps(core.RESOLUTIONS), cls='hidden', id='resolution_list')
            with div(id='content'):
                with div(id='plex_csv_form'):
                    h1('Import Plex Library')
                    h2('Upload Plex CSV')
                    with p():
                        input(type='file', placeholder='localhost', name='plex_csv', id='plex_csv')
                        with a(href='https://github.com/nosmokingbandit/Watcher3/wiki/Importing-from-other-applications#plex'):
                            i(cls='fa fa-question-circle')

                    with div(id='start_import_plex'):
                        i(cls='fa fa-upload')
                        span('Import Library')

                with div(id='plex_parsed_csv', cls='hidden'):
                    with div(id='plex_remote_map'):
                        h2('Remote paths')
                        p('Plex lists file locations relative to itself. If plex is on a '
                          'different device than Watcher you may need to alter file paths.')
                        with p('To alter a remote path, enter the information in the following '
                               'form and click Apply. Multiple changes can be applied. Use the '
                               'same principles as described in the '):
                            a('Wiki.', href='https://github.com/nosmokingbandit/Watcher3/wiki/Remote-Mapping')
                        p('Click Reset to return all paths to their original location.')
                        br()

                        with span('Local path: '):
                            input(id='plex_local_path', placeholder='//Movies/', type='text')
                        with span('Remote path: '):
                            input(id='plex_remote_path', placeholder='//Movies/', type='text')

                        button('Apply', id='plex_apply_remote')
                        button('Reset', id='plex_reset_remote')
                    with table(id='complete', cls='hidden'):
                        with tr():
                            th('Import', style='width: 1em; text-align: center;')
                            th('File')
                            th('Title')
                            th('ID', style='width: 1em;')
                            th('Source', style='width: 1em;')
                    with table(id='incomplete', cls='hidden'):
                        with tr():
                            th('Import', style='width: 1em; text-align: center;')
                            th('File')
                            th('Title')
                            th('IMDBID', style='width: 1em;')
                            th('Source', style='width: 1em;')
                    with span(id='plex_import'):
                        i(cls='fa fa-check-circle')
                        span('Import')

                with div(id='plex_wait_importing', cls='hidden'):
                    span('Importing selected movies.')
                    br()
                    span('This may take several minutes.')
                    br()
                    with span(id='import_progress'):
                        span(cls='progress_bar')
                    span(id='import_progress_text')

                with div(id='plex_import_results', cls='hidden'):
                    with table(id='plex_import_success', cls='hidden'):
                        span('Imported:')
                        with tr():
                            th('Title')
                            th('IMDB ID')
                    with table(id='plex_import_error', cls='hidden'):
                        with tr():
                            th('File')
                            th('Error')
                    with a(id='finished', href='{}/status'.format(core.URL_BASE), cls='hidden'):
                        i(cls='fa fa-thumbs-o-up')
                        span('Cool')

            with div(id='no_new_movies', cls='hidden'):
                h3('No new movies found')
                br()
                with a(href=core.URL_BASE+'/import_library'):
                    i(cls='fa fa-arrow-circle-left')
                    span('Return')

            div(id='thinker')
        return doc.render()

    @expose
    def couchpotato(self):
        doc = dominate.document(title='Watcher')
        doc.attributes['lang'] = 'en'

        with doc.head:
            Head.insert()
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/import_library.css?v=03.28')
            link(rel='stylesheet', href=core.URL_BASE + '/static/css/{}import_library.css?v=03.28'.format(core.CONFIG['Server']['theme']))
            script(type='text/javascript', src=core.URL_BASE + '/static/js/import_library/main.js?v=03.28')

        with doc:
            Header.insert_header(current=None)
            span(json.dumps(core.RESOLUTIONS), cls='hidden', id='resolution_list')
            span(json.dumps(list(core.CONFIG['Quality']['Profiles'].keys())), cls='hidden', id='profile_list')
            with div(id='content'):
                with div(id='cp_server_info'):
                    h1('Import CouchPotato Library')
                    h2('Enter CouchPotato server information:')
                    with p():
                        with select(id='scheme'):
                            option('http://', value='http://')
                            option('https://', value='https://')
                        input(type='text', placeholder='localhost', id='cp_address')
                        span(':')
                        input(type='number', placeholder='5050', id='cp_port')
                    with p('API Key'):
                        input(type='text', placeholder='123456789abcdef', id='cp_key', style='width: 18em;')

                    with div(id='start_import_cp'):
                        i(cls='fa fa-cloud-download')
                        span('Import Library')

                with div(id='cp_response', cls='hidden'):
                    h3('The following movies have been found')
                    h3('Please review this list before submitting')
                    br()
                    with table(id='finished', cls='hidden'):
                        h3('Finished movies')
                        with tr():
                            th('Import', style='width: 1em; text-align: center;')
                            th('Title')
                            th('IMDBID', style='width: 1em;')
                            th('Source', style='width: 1em;')

                    with table(id='wanted', cls='hidden'):
                        h3('Wanted movies')
                        with tr():
                            th('Import', style='width: 1em; text-align: center;')
                            th('Title')
                            th('IMDBID', style='width: 1em;')
                            th('Quality Profile', style='width: 1em;')
                    with span(id='cp_import'):
                        i(cls='fa fa-check-circle')
                        span('Import')

                with div(id='cp_wait_importing', cls='hidden'):
                    span('Importing selected movies.')
                    br()
                    span('This may take several minutes.')
                    br()
                    with span(id='import_progress'):
                        span(cls='progress_bar')
                    span(id='import_progress_text')

                with div(id='cp_import_results', cls='hidden'):
                    with table(id='cp_import_success', cls='hidden'):
                        span('Imported:')
                        with tr():
                            th('Title')
                            th('IMDB ID')
                    with table(id='cp_import_error', cls='hidden'):
                        with tr():
                            th('File')
                            th('Error')
                    with a(id='finished', href='{}/status'.format(core.URL_BASE), cls='hidden'):
                        i(cls='fa fa-thumbs-o-up')
                        span('Cool')

            with div(id='no_new_movies', cls='hidden'):
                h3('No new movies found')
                br()
                with a(href=core.URL_BASE+'/import_library'):
                    i(cls='fa fa-arrow-circle-left')
                    span('Return')

            div(id='thinker')
        return doc.render()

# pylama:ignore=W0401

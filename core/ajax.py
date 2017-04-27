import json
import logging
import os
import sys
import threading
import cherrypy
from base64 import b16encode
import core
from core import config, library, plugins, poster, searchresults, searcher, snatcher, sqldb, version
from core.providers import torrent, newznab
from core.downloaders import nzbget, sabnzbd, transmission, qbittorrent, deluge, rtorrent
from core.movieinfo import TMDB
from core.notification import Notification
from core.helpers import Conversions
from core.rss import predb
from templates import movie_info_popup, import_library, movie_status_popup, plugin_conf_popup, status
logging = logging.getLogger(__name__)


class Ajax(object):
    ''' These are all the methods that handle
        ajax post/get requests from the browser.

    Except in special circumstances, all should return a JSON string
        since that is the only datatype sent over http

    '''

    def __init__(self):
        self.tmdb = TMDB()
        self.config = config.Config()
        self.metadata = library.Metadata()
        self.predb = predb.PreDB()
        self.plugins = plugins.Plugins()
        self.searcher = searcher.Searcher()
        self.score = searchresults.Score()
        self.sql = sqldb.SQL()
        self.library = library
        self.poster = poster.Poster()
        self.snatcher = snatcher.Snatcher()
        self.update = library.Status()

    @cherrypy.expose
    def search_tmdb(self, search_term):
        ''' Search tmdb for movies
        :param search_term: str title and year of movie (Movie Title 2016)

        Returns str json-encoded list of dicts that contain tmdb's data.
        '''

        results = self.tmdb.search(search_term)
        if not results:
            logging.info('No Results found for {}'.format(search_term))
            return None
        else:
            return json.dumps(results)

    @cherrypy.expose
    def movie_info_popup(self, data):
        ''' Calls movie_info_popup to render html
        :param imdbid: str imdb identification number (tt123456)

        Returns str html content.
        '''

        mip = movie_info_popup.MovieInfoPopup()
        return mip.html(data)

    @cherrypy.expose
    def movie_status_popup(self, imdbid):
        ''' Calls movie_status_popup to render html
        :param imdbid: str imdb identification number (tt123456)

        Returns str html content.
        '''

        msp = movie_status_popup.MovieStatusPopup()
        return msp.html(imdbid)

    @cherrypy.expose
    def add_wanted_movie(self, data, full_metadata=False):
        ''' Adds movie to Wanted list.
        :param data: str json.dumps(dict) of info to add to database.
        full_metadata: bool if data is complete and ready for write

        data MUST inlcude tmdb id as data['id']

        Writes data to MOVIES table.

        If full_metadata is False, searches tmdb for data['id'] and updates data

        If Search on Add enabled,
            searches for movie immediately in separate thread.
            If Auto Grab enabled, will snatch movie if found.

        Returns str json.dumps(dict) of status and message
        '''

        def thread_search_grab(data):
            imdbid = data['imdbid']
            title = data['title']
            year = data['year']
            quality = data['quality']
            self.predb.check_one(data)
            if core.CONFIG['Search']['searchafteradd']:
                if self.searcher.search(imdbid, title, year, quality):
                    if core.CONFIG['Search']['autograb']:
                        self.snatcher.auto_grab(data)

        response = {}
        data = json.loads(data)
        tmdbid = data['id']

        if not full_metadata:
            movie = self.tmdb._search_tmdbid(tmdbid)[0]
            movie.update(data)
        else:
            movie = data

        movie['quality'] = data.get('quality', 'Default')
        movie['status'] = data.get('status', 'Waiting')

        if self.sql.row_exists('MOVIES', imdbid=movie['imdbid']):
            logging.info('{} already exists in library.'.format(movie['title']))

            response['response'] = False

            response['error'] = '{} already exists in library.'.format(movie['title'])
            return json.dumps(response)

        if movie.get('poster_path'):
            poster_url = 'http://image.tmdb.org/t/p/w300{}'.format(movie['poster_path'])
        else:
            poster_url = 'static/images/missing_poster.jpg'

        movie = self.metadata.convert_to_db(movie)

        if self.sql.write('MOVIES', movie):
            t2 = threading.Thread(target=self.poster.save_poster, args=(movie['imdbid'], poster_url))
            t2.start()

            if movie['status'] != 'Disabled' and movie['year'] != 'N/A':  # disable immediately grabbing new release for imports
                t = threading.Thread(target=thread_search_grab, args=(movie,))
                t.start()

            response['response'] = True
            response['message'] = '{} {} added to library.'.format(movie['title'], movie['year'])
            self.plugins.added(movie['title'], movie['year'], movie['imdbid'], movie['quality'])

            return json.dumps(response)
        else:
            response['response'] = False
            response['error'] = 'Could not write to database. Check logs for more information.'
            return json.dumps(response)

    @cherrypy.expose
    def add_wanted_imdbid(self, imdbid, quality='Default'):
        ''' Method to quckly add movie with just imdbid
        :param imdbid: str imdb id #

        Submits movie with base quality options

        Generally just used for the api

        Returns dict of success/fail with message.

        Returns str json.dumps(dict)
        '''

        response = {}

        movie = self.tmdb._search_imdbid(imdbid)

        if not movie:
            response['status'] = 'false'
            response['message'] = '{} not found on TMDB.'.format(imdbid)
            return response
        else:
            movie = movie[0]

        movie['imdbid'] = imdbid
        movie['quality'] = quality

        return self.add_wanted_movie(json.dumps(movie))

    @cherrypy.expose
    def add_wanted_tmdbid(self, tmdbid, quality='Default'):
        ''' Method to quckly add movie with just tmdbid
        :param imdbid: str imdb id #

        Submits movie with base quality options

        Generally just used for the api

        Returns dict of success/fail with message.

        Returns str json.dumps(dict)
        '''

        response = {}

        data = self.tmdb._search_tmdbid(tmdbid)

        if not data:
            response['status'] = 'false'
            response['message'] = '{} not found on TMDB.'.format(tmdbid)
            return response
        else:
            data = data[0]

        data['quality'] = quality
        data['status'] = 'Waiting'

        return self.add_wanted_movie(json.dumps(data))

    @cherrypy.expose
    def save_settings(self, data):
        ''' Saves settings to config file
        :param data: dict of Section with nested dict of keys and values:
        {'Section': {'key': 'val', 'key2': 'val2'}, 'Section2': {'key': 'val'}}

        All dicts must contain the full tree or data will be lost.

        Fires off additional methods if neccesary.

        Returns json.dumps(dict)
        '''

        # orig_config = dict(core.CONFIG)

        logging.info('Saving settings.')
        data = json.loads(data)

        save_data = {}
        for key in data:
            if data[key] != core.CONFIG[key]:
                save_data[key] = data[key]

        if not save_data:
            return json.dumps({'response': True})

        try:
            self.config.write_dict(save_data)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Writing config.', exc_info=True)
            return json.dumps({'response': False, 'error': 'Unable to write to config file.'})

        return json.dumps({'response': True})

    @cherrypy.expose
    def remove_movie(self, imdbid):
        ''' Removes movie
        :param imdbid: str imdb identification number (tt123456)

        Removes row from MOVIES, removes any entries in SEARCHRESULTS
        In separate thread deletes poster image.

        Returns srt 'error' or nothing on success
        '''

        t = threading.Thread(target=self.poster.remove_poster, args=(imdbid,))
        t.start()

        if self.sql.remove_movie(imdbid):
            response = {'response': True}
        else:
            response = {'response': False}
        return json.dumps(response)

    @cherrypy.expose
    def search(self, imdbid, title, year, quality):
        ''' Search indexers for specific movie.
        :param imdbid: str imdb identification number (tt123456)
        :param title: str movie title and year

        Checks predb, then, if found, starts searching providers for movie.

        Does not return
        '''

        self.searcher.search(imdbid, title, year, quality)
        return

    @cherrypy.expose
    def manual_download(self, title, year, guid, kind):
        ''' Sends search result to downloader manually
        :param guid: str download link for nzb/magnet/torrent file.
        :param kind: str type of download (torrent, magnet, nzb)

        Returns str json.dumps(dict) success/fail message
        '''

        torrent_enabled = core.CONFIG['Downloader']['Sources']['torrentenabled']

        usenet_enabled = core.CONFIG['Downloader']['Sources']['usenetenabled']

        if kind == 'nzb' and not usenet_enabled:
            return json.dumps({'response': False, 'error': 'Link is NZB but no Usent downloader is enabled.'})
        elif kind in ('torrent', 'magnet') and not torrent_enabled:
            return json.dumps({'response': False, 'error': 'Link is {} but no Torrent downloader is enabled.'.format(kind)})

        data = dict(self.sql.get_single_search_result('guid', guid))
        if data:
            data['year'] = year
            return json.dumps(self.snatcher.snatch(data))
        else:
            return json.dumps({'response': False, 'error': 'Unable to get download information from the database. Check logs for more information.'})

    @cherrypy.expose
    def mark_bad(self, guid, imdbid, cancel_download=False):
        ''' Marks guid as bad in SEARCHRESULTS and MARKEDRESULTS
        :param guid: str guid to mark
        :param imdbid: str imdbid # of movie to mark
        cancel_download: bool send command to download client to cancel download

        Returns str json.dumps(dict)
        '''

        if self.update.mark_bad(guid, imdbid=imdbid):
            response = {'response': True, 'message': 'Marked as Bad.'}
        else:
            response = {'response': False, 'error': 'Could not mark release as bad.'}

        if cancel_download:
            c = False
            r = self.sql.get_single_search_result('guid', guid)

            if r['status'] != 'Snatched':
                return json.dumps(response)

            client = r['download_client'] if r else None
            downloadid = r['downloadid'] if r else None
            if not client:
                logging.info('Download client not found, cannot cancel download.')
                return json.dumps(response)
            elif client == 'nzbget':
                c = nzbget.Nzbget.cancel_download(downloadid)
            elif client == 'sabnzbd':
                c = sabnzbd.Sabnzbd.cancel_download(downloadid)
            elif client == 'qbittorrent':
                c = qbittorrent.QBittorrent.cancel_download(downloadid)
            elif client == 'delugerpc':
                c = deluge.DelugeRPC.cancel_download(downloadid)
            elif client == 'delugeweb':
                logging.warning('DelugeWeb API does not support torrent removal.')
            elif client == 'transmission':
                c = transmission.Transmission.cancel_download(downloadid)
            elif client == 'rtorrentscgi':
                c = rtorrent.rTorrentSCGI.cancel_download(downloadid)
            elif client == 'rtorrenthttp':
                c = rtorrent.rTorrentHTTP.cancel_download(downloadid)

            if not c:
                response['response'] = False
                response['error'] = response.get('error', '') + ' Could not remove download from client.'

        return json.dumps(response)

    @cherrypy.expose
    def notification_remove(self, index):
        ''' Removes notification from core.notification
        :param index: str or unicode index of notification to remove

        'index' will be a type of string since it comes from ajax request.
            Therefore we convert to int here before passing to Notification

        Simply calls Notification module.

        Does not return
        '''

        Notification.remove(int(index))

        return

    @cherrypy.expose
    def update_check(self):
        ''' Manually check for updates

        Returns str json.dumps(dict) from Version manager update_check()
        '''

        response = version.Version().manager.update_check()
        return json.dumps(response)

    @cherrypy.expose
    def refresh_list(self, list, imdbid='', quality=''):
        ''' Re-renders html for Movies/Results list
        :param list: str the html list id to be re-rendered
        :param imdbid: str imdb identification number (tt123456) <optional>

        Calls template file to re-render a list when modified in the database.
        #result_list requires imdbid.

        Returns str html content.
        '''

        if list == '#movie_list':
            return status.Status.movie_list()
        if list == '#result_list':
            return movie_status_popup.MovieStatusPopup().result_list(imdbid, quality)

    @cherrypy.expose
    def test_downloader_connection(self, mode, data):
        ''' Test connection to downloader.
        :param mode: str which downloader to test.
        :param data: dict connection information (url, port, login, etc)

        Executes staticmethod in the chosen downloader's class.

        Returns str json.dumps dict:
        {'status': 'false', 'message': 'this is a message'}
        '''

        response = {}

        data = json.loads(data)

        if mode == 'sabnzbd':
            test = sabnzbd.Sabnzbd.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test
        if mode == 'nzbget':
            test = nzbget.Nzbget.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'transmission':
            test = transmission.Transmission.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'delugerpc':
            test = deluge.DelugeRPC.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'delugeweb':
            test = deluge.DelugeWeb.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'qbittorrent':
            test = qbittorrent.QBittorrent.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'rtorrentscgi':
            test = rtorrent.rTorrentSCGI.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        if mode == 'rtorrenthttp':
            test = rtorrent.rTorrentHTTP.test_connection(data)
            if test is True:
                response['status'] = True
                response['message'] = 'Connection successful.'
            else:
                response['status'] = False
                response['error'] = test

        return json.dumps(response)

    @cherrypy.expose
    def server_status(self, mode):
        ''' Check or modify status of CherryPy server_status
        :param mode: str command or request of state

        Restarts or Shuts Down server in separate thread.
            Delays by one second to allow browser to redirect.

        If mode == 'online', asks server for status.
            (ENGINE.started, ENGINE.stopped, etc.)

        Returns nothing for mode == restart || shutdown
        Returns str server state if mode == online
        '''

        def server_restart():
            cwd = os.getcwd()
            cherrypy.engine.restart()
            os.chdir(cwd)  # again, for the daemon
            return

        def server_shutdown():
            cherrypy.engine.stop()
            cherrypy.engine.exit()
            sys.exit(0)

        if mode == 'restart':
            logging.info('Restarting Server...')
            threading.Timer(1, server_restart).start()
            return

        elif mode == 'shutdown':
            logging.info('Shutting Down Server...')
            threading.Timer(1, server_shutdown).start()
            return

        elif mode == 'online':
            return str(cherrypy.engine.state)

    @cherrypy.expose
    def update_now(self, mode):
        ''' Starts and executes update process.
        :param mode: str 'set_true' or 'update_now'

        The ajax response is a generator that will contain
            only the success/fail message.

        This is done so the message can be passed to the ajax
            request in the browser while cherrypy restarts.
        '''

        response = self._update_now(mode)
        for i in response:
            return i

    @cherrypy.expose
    def _update_now(self, mode):
        ''' Starts and executes update process.
        :param mode: str 'set_true' or 'update_now'

        Helper for self.update_now()

        If mode == set_true, sets core.UPDATING to True
        This is done so if the user visits /update without setting true
            they will be redirected back to status.
        Yields 'true' back to browser

        If mode == 'update_now', starts update process.
        Yields 'true' or 'failed'. If true, restarts server.
        '''

        if mode == 'set_true':
            core.UPDATING = True
            yield json.dumps({'response': True})
        if mode == 'update_now':
            update_status = version.Version().manager.execute_update()
            core.UPDATING = False
            if update_status is False:
                logging.error('Update Failed.')
                yield json.dumps({'response': False})
            elif update_status is True:
                yield json.dumps({'response': True})
                logging.info('Respawning process...')
                cherrypy.engine.stop()
                python = sys.executable
                os.execl(python, python, *sys.argv)
        else:
            return

    @cherrypy.expose
    def update_movie_options(self, quality, status, imdbid):
        ''' Updates quality settings for individual title
        :param quality: str name of new quality
        :param status: str status management state
        :param imdbid: str imdb identification number

        '''

        logging.info('Updating quality profile to {} for {}.'.format(quality, imdbid))

        if not self.sql.update('MOVIES', 'quality', quality, 'imdbid', imdbid):
            return json.dumps({'response': False})

        logging.info('Updating status to {} for {}.'.format(status, imdbid))

        if status == 'Automatic':
            if not self.update.movie_status(imdbid):
                return json.dumps({'response': False})
        elif status == 'Finished':
            if not self.sql.update('MOVIES', 'status', 'Disabled', 'imdbid', imdbid):
                return json.dumps({'response': False})

        return json.dumps({'response': True})

    @cherrypy.expose
    def get_log_text(self, logfile):

        with open(os.path.join(core.LOG_DIR, logfile), 'r') as f:
            log_text = ''.join(reversed(f.readlines()))

        return log_text

    @cherrypy.expose
    def indexer_test(self, indexer, apikey, mode):
        if mode == 'newznab':
            return json.dumps(newznab.NewzNab.test_connection(indexer, apikey))
        elif mode == 'torznab':
            return json.dumps(torrent.Torrent.test_connection(indexer, apikey))
        else:
            return json.dumps({'response': 'false', 'error': 'Invalid test mode.'})

    @cherrypy.expose
    def get_plugin_conf(self, folder, conf):
        ''' Calls plugin_conf_popup to render html
        folder: str folder to read config file from
        conf: str filename of config file (ie 'my_plugin.conf')

        Returns str html content.
        '''

        return plugin_conf_popup.PluginConfPopup.html(folder, conf)

    @cherrypy.expose
    def save_plugin_conf(self, folder, conf, data):
        ''' Calls plugin_conf_popup to render html
        folder: str folder to store config file
        conf: str filename of config file (ie 'my_plugin.conf')
        data: str json data to store in conf file

        Returns str json dumps dict of success/fail message
        '''

        data = json.loads(data)

        conf_file = conf_file = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, folder, conf)

        response = {'response': True, 'message': 'Plugin settings saved'}

        try:
            with open(conf_file, 'w') as output:
                json.dump(data, output, indent=2)
        except Exception as e:
            response = {'response': False, 'error': str(e)}

        return json.dumps(response)

    @cherrypy.expose
    def scan_library_directory(self, directory, minsize, recursive):
        ''' Calls library to scan directory for movie files
        directory: str directory to scan
        minsize: str minimum file size in mb, coerced to int
        resursive: str 'true' or 'false', coerced to bool

        Removes all movies already in library.

        If error, yields {'error': reason} and stops Iteration
        If movie has all metadata, yields:
            {'complete': {<metadata>}}
        If missing imdbid or resolution, yields:
            {'incomplete': {<knownn metadata>}}

        All metadata dicts include:
            'path': 'absolute path to file'
            'progress': '10 of 250'

        Yeilds generator object of json objects
        '''

        recursive = json.loads(recursive)
        minsize = int(minsize)
        files = self.library.ImportDirectory.scan_dir(directory, minsize, recursive)
        if files.get('error'):
            yield json.dumps({'error': files['error']})
            raise StopIteration()
        library = [i['imdbid'] for i in self.sql.get_user_movies()]
        files = files['files']
        length = len(files)
        for index, path in enumerate(files):
            metadata = self.metadata.get_metadata(path)
            metadata['size'] = os.path.getsize(path)
            metadata['finished_file'] = path
            metadata['human_size'] = Conversions.human_file_size(metadata['size'])
            progress = [index + 1, length]
            if not metadata.get('imdbid'):
                logging.info('IMDB unknown for import {}'.format(metadata['title']))
                yield json.dumps({'response': 'incomplete', 'movie': metadata, 'progress': progress})
                continue
            if metadata['imdbid'] in library:
                logging.info('Import {} already in library, ignoring.'.format(metadata['title']))
                yield json.dumps({'response': 'in_library', 'movie': metadata, 'progress': progress})
                continue
            elif not metadata.get('resolution'):
                logging.info('Resolution/Source unknown for import {}'.format(metadata['title']))
                yield json.dumps({'response': 'incomplete', 'movie': metadata, 'progress': progress})
                continue
            else:
                logging.info('All data found for import {}'.format(metadata['title']))
                yield json.dumps({'response': 'complete', 'movie': metadata, 'progress': progress})

    scan_library_directory._cp_config = {'response.stream': True}

    @cherrypy.expose
    def import_dir(self, movie_data, corrected_movies):
        ''' Imports list of movies in data
        movie_data: list of dicts of movie info ready to import
        corrected_movies: list of dicts of user-corrected movie info

        corrected_movies must be [{'/path/to/file': {'known': 'metadata'}}]

        Iterates through corrected_movies and attmpts to get metadata again if required.

        If imported, generates and stores fake search result.

        Creates dict {'success': [], 'failed': []} and
            appends movie data to the appropriate list.

        Yeilds generator object of json objects
        '''

        movie_data = json.loads(movie_data)
        corrected_movies = json.loads(corrected_movies)

        fake_results = []

        success = []

        length = len(movie_data) + len(corrected_movies)
        progress = 1

        if corrected_movies:
            for data in corrected_movies:
                tmdbdata = self.tmdb._search_imdbid(data['imdbid'])[0]
                if tmdbdata:
                    data['year'] = tmdbdata['release_date'][:4]
                    data.update(tmdbdata)
                    movie_data.append(data)
                else:
                    logging.error('Unable to find {} on TMDB.'.format(data['imdbid']))
                    yield json.dumps({'response': False, 'movie': data, 'progress': [progress, length], 'reason': 'Unable to find {} on TMDB.'.format(data['imdbid'])})
                    progress += 1

        for movie in movie_data:
            if movie['imdbid']:
                movie['status'] = 'Disabled'
                movie['predb'] = 'found'
                response = json.loads(self.add_wanted_movie(json.dumps(movie)))
                if response['response'] is True:
                    fake_results.append(searchresults.generate_simulacrum(movie))
                    yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                    progress += 1
                    success.append(movie)
                    continue
                else:
                    yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': response['error']})
                    progress += 1
                    continue
            else:
                logging.error('Unable to find {} on TMDB.'.format(movie['imdbid']))
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': 'IMDB ID invalid or missing.'})
                progress += 1

        fake_results = self.score.score(fake_results, imported=True)

        for i in success:
            score = None
            for r in fake_results:
                if r['imdbid'] == i['imdbid']:
                    score = r['score']
                    break

            if score:
                self.sql.update('MOVIES', 'finished_score', score, 'imdbid', i['imdbid'])

        self.sql.write_search_results(fake_results)

    import_dir._cp_config = {'response.stream': True}

    @cherrypy.expose
    def list_files(self, current_dir, move_dir):
        ''' Lists files in directory
        current_dir: str base path
        move_dir: str child path to read

        Joins and normalizes paths:
            ('/home/user/movies', '..')
            Becomes /home/user

        Sends path to import_library template to generate html

        Returns json dict {'new_path': '/path', 'html': '<li>...'}
        '''

        response = {}

        new_path = os.path.normpath(os.path.join(current_dir, move_dir))
        response['new_path'] = new_path

        try:
            response['html'] = import_library.ImportLibrary.file_list(new_path)
        except Exception as e:
            response = {'error': str(e)}
            logging.error('Error listing directory.', exc_info=True)

        return json.dumps(response)

    @cherrypy.expose
    def update_metadata(self, imdbid, tmdbid=None):
        ''' Re-downloads metadata for each imdbid
        imdbid: str imdbid of movie
        tmdbid: str tmdbid of movie     <optional, default None>

        If tmdbid is None, looks in database for tmdbid using imdbid.
        If that fails, looks on tmdb api for imdbid
        If that fails returns error message

        '''

        movie = self.sql.get_movie_details('imdbid', imdbid)

        if tmdbid is None:
            tmdbid = movie.get('tmdbid')

            if not tmdbid:
                tmdbid = self.tmdb._search_imdbid(imdbid)[0].get('id')
            if not tmdbid:
                return json.dumps({'response': False, 'error': 'Unable to find {} on TMDB.'.format(imdbid)})

        new_data = self.tmdb._search_tmdbid(tmdbid)[0]
        new_data.pop('status')

        target_poster = os.path.join(self.poster.poster_folder, '{}.jpg'.format(imdbid))

        if new_data['poster_path']:
            poster_url = 'http://image.tmdb.org/t/p/w300{}'.format(new_data['poster_path'])
        else:
            poster_url = '{}/static/images/missing_poster.jpg'.format(core.PROG_PATH)

        if os.path.isfile(target_poster):
            try:
                os.remove(target_poster)
            except Exception as e: #noqa
                logging.warning('Unable to remove existing poster.', exc_info=True)
                return json.dumps({'response': False, 'error': 'Unable to remove existing poster.'})

        movie.update(new_data)
        movie = self.metadata.convert_to_db(movie)

        self.sql.update_multiple('MOVIES', movie, imdbid=imdbid)

        self.poster.save_poster(imdbid, poster_url)
        return json.dumps({'response': True, 'message': 'Metadata updated.'})

    @cherrypy.expose
    def change_quality_profile(self, profiles, imdbid=None):
        ''' Updates quality profile name
        profiles: dict of profile names. k:v is currentname:newname
        imdbid: str imdbid of movie to change   <default None>

        Changes movie quality profiles from k in names to v in names

        If imdbid is passed will change only one movie, otherwise changes
            all movies where profile == k

        If imdbid is passed and names contains more than one k:v pair, submits changes
            using v from the first dict entry. This is unreliable, so just submit one.

        Executes two loops.
            First changes qualities to temporary value.
            Then changes tmp values to target values.
        This way you can swap two names without them all becoming one.

        '''

        profiles = json.loads(profiles)

        if imdbid:
            q = list(profiles.values())[0]

            if not self.sql.update('MOVIES', 'quality', q, 'imdbid', imdbid):
                return json.dumps({'response': False, 'error': 'Unable to update {} to quality {}'.format(imdbid, q)})
            else:
                return json.dumps({'response': True, 'Message': '{} changed to {}'.format(imdbid, q)})
        else:
            tmp_qualities = {}
            for k, v in profiles.items():
                q = b16encode(v.encode('ascii')).decode('ascii')
                if not self.sql.update('MOVIES', 'quality', q, 'quality', k):
                    return json.dumps({'response': False, 'error': 'Unable to change {} to temporary quality {}'.format(k, q)})
                else:
                    tmp_qualities[q] = v

            for k, v in tmp_qualities.items():
                if not self.sql.update('MOVIES', 'quality', v, 'quality', k):
                    return json.dumps({'response': False, 'error': 'Unable to change temporary quality {} to {}'.format(k, v)})
                if not self.sql.update('MOVIES', 'backlog', 0, 'quality', k):
                    return json.dumps({'response': False, 'error': 'Unable to set backlog flag. Manual backlog search required for affected titles.'})

            return json.dumps({'response': True, 'message': 'Quality profiles updated.'})

    @cherrypy.expose
    def get_kodi_movies(self, url):
        ''' Gets list of movies from kodi server
        url: str url of kodi server

        Calls Kodi import method to gather list.

        Returns list of dicts of movies
        '''

        return json.dumps(library.ImportKodiLibrary.get_movies(url))

    @cherrypy.expose
    def import_kodi(self, movies):
        ''' Imports list of movies in movies from Kodi library
        movie_data: JSON list of dicts of movies

        Iterates through movies and gathers all required metadata.

        If imported, generates and stores fake search result.

        Creates dict {'success': [], 'failed': []} and
            appends movie data to the appropriate list.

        Yeilds generator object of json objects
        '''

        movies = json.loads(movies)

        fake_results = []

        success = []

        length = len(movies)
        progress = 1

        for movie in movies:

            tmdb_data = self.tmdb._search_imdbid(movie['imdbid'])[0]
            if not tmdb_data.get('id'):
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': 'Unable to find {} on TMDB.'.format(movie['imdbid'])})
                progress += 1
                continue
            else:
                movie['id'] = tmdb_data['id']
                movie['size'] = 0
                movie['status'] = 'Disabled'
                movie['predb'] = 'found'

            response = json.loads(self.add_wanted_movie(json.dumps(movie)))
            if response['response'] is True:
                fake_results.append(searchresults.generate_simulacrum(movie))
                yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                progress += 1
                success.append(movie)
                continue
            else:
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': response['error']})
                progress += 1
                continue

        fake_results = self.score.score(fake_results, imported=True)

        for i in success:
            score = None
            for r in fake_results:
                if r['imdbid'] == i['imdbid']:
                    score = r['score']
                    break

            if score:
                self.sql.update('MOVIES', 'finished_score', score, 'imdbid', i['imdbid'])

        self.sql.write_search_results(fake_results)

    import_kodi._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_plex_libraries(self, server, username, password):
        if core.CONFIG['External']['plex_tokens'].get(server) is None:
            token = library.ImportPlexLibrary.get_token(username, password)
            if token is None:
                return json.dumps({'response': False, 'error': 'Unable to get Plex token.'})
            else:
                core.CONFIG['External']['plex_tokens'][server] = token
                self.config.dump(core.CONFIG)
        else:
            token = core.CONFIG['External']['plex_tokens'][server]

        return json.dumps(library.ImportPlexLibrary.get_libraries(server, token))

    @cherrypy.expose
    def upload_plex_csv(self, file_input):
        try:
            csv_text = file_input.file.read().decode('utf-8')
            file_input.file.close()
        except Exception as e: #noqa
            print(e)
            return

        if csv_text:
            return json.dumps(library.ImportPlexLibrary.read_csv(csv_text))

        return

    @cherrypy.expose
    def import_plex_csv(self, movie_data, corrected_movies):
        ''' Imports list of movies genrated by csv import
        movie_data: list of dicts of movie info ready to import
        corrected_movies: list of dicts of user-corrected movie info

        Iterates through corrected_movies and attmpts to get metadata again if required.

        If imported, generates and stores fake search result.

        Creates dict {'success': [], 'failed': []} and
            appends movie data to the appropriate list.

        Yeilds generator object of json objects
        '''

        movie_data = json.loads(movie_data)
        corrected_movies = json.loads(corrected_movies)

        fake_results = []

        success = []

        length = len(movie_data) + len(corrected_movies)
        progress = 1

        if corrected_movies:
            for data in corrected_movies:
                tmdbdata = self.tmdb._search_imdbid(data['imdbid'])[0]
                if tmdbdata:
                    data['year'] = tmdbdata['release_date'][:4]
                    data.update(tmdbdata)
                    movie_data.append(data)
                else:
                    logging.error('Unable to find {} on TMDB.'.format(data['imdbid']))
                    yield json.dumps({'response': False, 'movie': data, 'progress': [progress, length], 'reason': 'Unable to find {} on TMDB.'.format(data['imdbid'])})
                    progress += 1

        for movie in movie_data:
            if movie['imdbid']:
                movie['status'] = 'Disabled'
                movie['predb'] = 'found'

                tmdb_data = self.tmdb._search_imdbid(movie['imdbid'])[0]
                movie.update(tmdb_data)
                response = json.loads(self.add_wanted_movie(json.dumps(movie)))
                if response['response'] is True:
                    fake_results.append(searchresults.generate_simulacrum(movie))
                    yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                    progress += 1
                    success.append(movie)
                    continue
                else:
                    yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': response['error']})
                    progress += 1
                    continue
            else:
                logging.error('Unable to find {} on TMDB.'.format(movie['imdbid']))
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': 'IMDB ID invalid or missing.'})
                progress += 1

        fake_results = self.score.score(fake_results, imported=True)

        for i in success:
            score = None
            for r in fake_results:
                if r['imdbid'] == i['imdbid']:
                    score = r['score']
                    break

            if score:
                self.sql.update('MOVIES', 'finished_score', score, 'imdbid', i['imdbid'])

        self.sql.write_search_results(fake_results)

    import_dir._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cp_movies(self, url, apikey):

        url = '{}/api/{}/movie.list/'.format(url, apikey)

        return json.dumps(library.ImportCPLibrary.get_movies(url))

    @cherrypy.expose
    def import_cp_movies(self, wanted, finished):
        wanted = json.loads(wanted)
        finished = json.loads(finished)

        fake_results = []

        success = []

        length = len(wanted) + len(finished)
        progress = 1

        for movie in wanted:
            response = json.loads(self.add_wanted_movie(json.dumps(movie), full_metadata=True))
            if response['response'] is True:
                yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                progress += 1
                continue
            else:
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': response['error']})
                progress += 1
                continue

        for movie in finished:
            movie['predb'] = 'found'
            movie['status'] = 'Disabled'

            response = json.loads(self.add_wanted_movie(json.dumps(movie), full_metadata=True))
            if response['response'] is True:
                fake_results.append(searchresults.generate_simulacrum(movie))
                yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                progress += 1
                success.append(movie)
                continue
            else:
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'reason': response['error']})
                progress += 1
                continue

        fake_results = self.score.score(fake_results, imported=True)

        for i in success:
            score = None
            for r in fake_results:
                if r['imdbid'] == i['imdbid']:
                    score = r['score']
                    break

            if score:
                self.sql.update('MOVIES', 'finished_score', score, 'imdbid', i['imdbid'])

        self.sql.write_search_results(fake_results)
    import_cp_movies._cp_config = {'response.stream': True}

    @cherrypy.expose
    def manager_update_metadata(self, movies):
        movies = json.loads(movies)

        response = {'response': True, 'errors': []}
        for i in movies:
            r = json.loads(self.update_metadata(i['imdbid'], tmdbid=i['tmdbid']))

            if r['response'] is False:
                response['response'] = False
                response['errors'].append({i['imdbid']: r['error']})

        return json.dumps(response)

    @cherrypy.expose
    def manager_change_quality(self, movies, quality):
        movies = json.loads(movies)

        response = {'response': True, 'errors': []}
        for i in movies:
            imdbid = i['imdbid']
            r = json.loads(self.change_quality_profile(json.dumps({'Default': quality}), imdbid=imdbid))

            if r['response'] is False:
                response['response'] = False
                response['errors'].append({'imdbid': imdbid, 'error': r['error']})

        return json.dumps(response)

    @cherrypy.expose
    def manager_remove_movies(self, movies):
        movies = json.loads(movies)

        response = {'response': True, 'errors': []}
        for i in movies:
            r = json.loads(self.remove_movie(i['imdbid']))

            if r['response'] is False:
                response['response'] = False
                response['errors'].append(i['imdbid'])

        return json.dumps(response)

    @cherrypy.expose
    def manager_reset_movies(self, movies):
        movies = json.loads(movies)

        response = {'response': True, 'errors': []}
        for i in movies:
            imdbid = i['imdbid']
            if not self.sql.purge_search_results(imdbid):
                response['response'] = False
                response['errors'].append({imdbid: 'Unable to purge Search Results'})
                continue
            db_reset = {'quality': 'Default',
                        'status': 'Waiting',
                        'finished_date': None,
                        'finished_score': None,
                        'backlog': 0,
                        'finished_file': None
                        }
            if not self.sql.update_multiple('MOVIES', db_reset, imdbid=imdbid):
                    response['response'] = False
                    response['errors'].append({imdbid: 'Unable to update Database'})
                    continue
            response['response'] = False
            response['errors'].append({'imdbid': imdbid, 'error': 'THIS IS A TEST'})

        return json.dumps(response)

    @cherrypy.expose
    def generate_stats(self):
        return json.dumps(self.update.get_stats())

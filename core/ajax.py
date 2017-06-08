import json
import logging
import os
import sys
import threading
import cherrypy
from base64 import b16encode
import core
from core import config, library, plugins, searchresults, searcher, snatcher, sqldb, version
from core.providers import torrent, newznab
from core.downloaders import nzbget, sabnzbd, transmission, qbittorrent, deluge, rtorrent
from core.movieinfo import TMDB, Trailer
from core.notification import Notification
from core.helpers import Conversions
from core.rss import predb
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
        self.poster = library.Poster()
        self.snatcher = snatcher.Snatcher()
        self.manage = library.Manage()

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
    def get_search_results(self, imdbid, quality=None):
        ''' Gets search results for movie
        imdbid: str imdb identification number (tt123456)

        Passes request to sql.get_search_results() then filters out unused download methods.

        Returns str json-encoded list of dicts
        '''

        results = self.sql.get_search_results(imdbid, quality=quality)

        if not core.CONFIG['Downloader']['Sources']['usenetenabled']:
            results = [res for res in results if res.get('type') != 'nzb']
        if not core.CONFIG['Downloader']['Sources']['torrentenabled']:
            results = [res for res in results if res.get('type') != 'torrent']

        if not results:
            return json.dumps({'response': False, 'next': Conversions.human_datetime(core.NEXT_SEARCH)});
        else:
            for i in results:
                i['size'] = Conversions.human_file_size(i['size'])
            return json.dumps({'response': True, 'results': results})

    @cherrypy.expose
    def get_trailer(self, title, year):
        return Trailer.get_trailer('{} {}'.format(title, year))

    @cherrypy.expose
    def movie_status_popup(self, imdbid):
        ''' Calls movie_status_popup to render html
        :param imdbid: str imdb identification number (tt123456)

        Returns str html content.
        '''

        res = self.sql.get_search_results(imdbid, quality=quality)
        return json.jumps(res)

    @cherrypy.expose
    def add_wanted_movie(self, data, origin='Search', full_metadata=False):
        ''' Adds movie to library
        data: dict of known movie data
        full_metadata: bool if data is complete for database

        Calls library.Manage.add_movie to add to library.
        If add is successful, movie is not an import, and has a year, starts
            search/grab method in separate thread

        '''
        data = json.loads(data)

        def thread_search_grab(data):
            imdbid = data['imdbid']
            title = data['title']
            year = data['year']
            quality = data['quality']
            if self.predb.backlog_search(data) and core.CONFIG['Search']['searchafteradd']:
                if self.searcher.search(imdbid, title, year, quality):
                    if core.CONFIG['Search']['autograb']:
                        best_release = self.snatcher.best_release(data)
                        if best_release:
                            self.snatcher.download(best_release)

        r = self.manage.add_movie(data, origin=origin, full_metadata=full_metadata)

        if r['response'] is True and r['movie']['status'] != 'Disabled' and r['movie']['year'] != 'N/A':  # disable immediately grabbing new release for imports
            t = threading.Thread(target=thread_search_grab, args=(r['movie'],))
            t.start()

        r.pop('movie', None)

        return json.dumps(r)

    @cherrypy.expose
    def save_settings(self, data):
        ''' Saves settings to config file
        :param data: dict of Section with nested dict of keys and values:
        {'Section': {'key': 'val', 'key2': 'val2'}, 'Section2': {'key': 'val'}}

        All dicts must contain the full tree or data will be lost.

        Fires off additional methods if neccesary.

        Returns json.dumps(dict)
        '''

        logging.info('Saving settings.')
        data = json.loads(data)

        save_data = {}
        for key in data:
            if data[key] != core.CONFIG[key]:
                save_data[key] = data[key]

        if not save_data:
            return json.dumps({'response': True})

        try:
            self.config.write(save_data)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:  # noqa
            logging.error('Writing config.', exc_info=True)
            return json.dumps({'response': False, 'error': 'Unable to write to config file.'})

        return json.dumps({'response': True})

    @cherrypy.expose
    def remove_movie(self, imdbid):
        ''' Removes movie
        :param imdbid: str imdb identification number (tt123456)

        Removes row from MOVIES, removes any entries in SEARCHRESULTS
        In separate thread deletes poster image.

        Returns str json dict
        '''

        t = threading.Thread(target=self.poster.remove_poster, args=(imdbid,))
        t.start()

        removed = self.sql.remove_movie(imdbid)

        if removed is True:
            response = {'response': True, 'removed': imdbid}
        elif removed is False:
            response = {'response': False, 'error': 'unable to remove {}'.format(imdbid)}
        elif removed is None:
            response = {'response': False, 'error': '{} does not exist'.format(imdbid)}

        return json.dumps(response)

    @cherrypy.expose
    def search(self, imdbid):
        ''' Search indexers for specific movie.
        :param imdbid: str imdb identification number (tt123456)

        Gets movie data from database and sends to searcher.search()

        Returns str json dict
        '''

        movie = self.sql.get_movie_details("imdbid", imdbid)

        if not movie:
            return json.dumps({'response': False, 'error': 'Unable to get info for imdb {}'.format(imdbid)})
        else:
            success = self.searcher.search(imdbid, movie['title'], movie['year'], movie['quality'])
            movie = self.sql.get_movie_details("imdbid", imdbid)

            if success:
                results = self.sql.get_search_results(imdbid, movie['quality'])
                for i in results:
                    i['size'] = Conversions.human_file_size(i['size'])
                return json.dumps({'response': True, 'results': results, 'movie_status': movie['status'], 'next': Conversions.human_datetime(core.NEXT_SEARCH)})
            else:
                return json.dumps({'response': False, 'error': 'Unable to complete search for imdb {}'.format(imdbid), 'movie_status': movie['status']})

    @cherrypy.expose
    def manual_download(self, year, guid, kind):
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
            return json.dumps(self.snatcher.download(data))
        else:
            return json.dumps({'response': False, 'error': 'Unable to get download information from the database. Check logs for more information.'})

    @cherrypy.expose
    def mark_bad(self, guid, imdbid, cancel_download=False):
        ''' Marks guid as bad in SEARCHRESULTS and MARKEDRESULTS
        :param guid: str guid to mark
        :param imdbid: str imdbid # of movie to mark
        cancel_download: bool send command to download client to cancel download

        Returns str json.dumps(dict) with keys response, error (if response is False), movie_status
        '''

        sr = self.manage.searchresults(guid, 'Bad')
        self.manage.markedresults(guid, 'Bad', imdbid=imdbid)

        if sr:
            response = {'response': True, 'message': 'Marked as Bad.'}
        else:
            response = {'response': False, 'error': 'Could not mark release as bad.'}

        response['movie_status'] = self.manage.movie_status(imdbid)
        if response['movie_status'] is False:
            response['error'] = response.get('error', '') + ' Could not set movie\'s status.'

        if cancel_download:
            cancelled = False
            r = self.sql.get_single_search_result('guid', guid)

            if r['status'] != 'Snatched':
                return json.dumps(response)

            client = r['download_client'] if r else None
            downloadid = r['downloadid'] if r else None
            if not client:
                logging.info('Download client not found, cannot cancel download.')
                return json.dumps(response)
            elif client == 'nzbget':
                cancelled = nzbget.Nzbget.cancel_download(downloadid)
            elif client == 'sabnzbd':
                cancelled = sabnzbd.Sabnzbd.cancel_download(downloadid)
            elif client == 'qbittorrent':
                cancelled = qbittorrent.QBittorrent.cancel_download(downloadid)
            elif client == 'delugerpc':
                cancelled = deluge.DelugeRPC.cancel_download(downloadid)
            elif client == 'delugeweb':
                logging.warning('DelugeWeb API does not support torrent removal.')
            elif client == 'transmission':
                cancelled = transmission.Transmission.cancel_download(downloadid)
            elif client == 'rtorrentscgi':
                cancelled = rtorrent.rTorrentSCGI.cancel_download(downloadid)
            elif client == 'rtorrenthttp':
                cancelled = rtorrent.rTorrentHTTP.cancel_download(downloadid)

            if not cancelled:
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
        elif mode == 'nzbget':
            test = nzbget.Nzbget.test_connection(data)
        elif mode == 'transmission':
            test = transmission.Transmission.test_connection(data)
        elif mode == 'delugerpc':
            test = deluge.DelugeRPC.test_connection(data)
        elif mode == 'delugeweb':
            test = deluge.DelugeWeb.test_connection(data)
        elif mode == 'qbittorrent':
            test = qbittorrent.QBittorrent.test_connection(data)
        elif mode == 'rtorrentscgi':
            test = rtorrent.rTorrentSCGI.test_connection(data)
        elif mode == 'rtorrenthttp':
            test = rtorrent.rTorrentHTTP.test_connection(data)

        if test is True:
            response['response'] = True
            response['message'] = 'Connection successful.'
        else:
            response['response'] = False
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
            cherrypy.engine.stop()
            python = sys.executable
            os.execl(python, python, *sys.argv)
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
            if not self.sql.update('MOVIES', 'status', 'Waiting', 'imdbid', imdbid):
                return json.dumps({'response': False})
            new_status = self.manage.movie_status(imdbid)
            if not new_status:
                return json.dumps({'response': False})
            else:
                return json.dumps({'response': True, 'status': new_status})
        elif status == 'Disabled':
            if not self.sql.update('MOVIES', 'status', 'Disabled', 'imdbid', imdbid):
                return json.dumps({'response': False})
            else:
                return json.dumps({'response': True, 'status': 'Disabled'})

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

        try:
            with open(os.path.join(core.PLUGIN_DIR, folder, conf)) as f:
                config = json.load(f)
            return json.dumps(config)
        except Exception as e:
            logging.error("Unable to read config file.", exc_info=True)
            return None

    @cherrypy.expose
    def save_plugin_conf(self, folder, filename, config):
        ''' Calls plugin_conf_popup to render html
        folder: str folder to store config file
        filename: str filename of config file (ie 'my_plugin.conf')
        config: str json data to store in conf file

        Returns str json dumps dict of success/fail message
        '''

        config = json.loads(config)

        conf_file = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, folder, filename)

        response = {'response': True, 'message': 'Plugin settings saved'}

        try:
            with open(conf_file, 'w') as output:
                json.dump(config, output, indent=2)
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
        files = core.library.ImportDirectory.scan_dir(directory, minsize, recursive)
        if files.get('error'):
            yield json.dumps({'error': files['error']})
            raise StopIteration()
        library = [i['imdbid'] for i in self.sql.get_user_movies()]
        files = files['files']
        length = len(files)

        if length == 0:
            yield json.dumps({'response': None})
            raise StopIteration()

        for index, path in enumerate(files):
            metadata = self.metadata.from_file(path)
            metadata['size'] = os.path.getsize(path)
            metadata['finished_file'] = path
            metadata['human_size'] = Conversions.human_file_size(metadata['size'])
            progress = [index + 1, length]
            if not metadata.get('imdbid'):
                metadata['imdbid'] = ''
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
    def import_dir(self, movies, corrected_movies):
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

        movie_data = json.loads(movies)
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
                    yield json.dumps({'response': False, 'movie': data, 'progress': [progress, length], 'error': 'Unable to find {} on TMDB.'.format(data['imdbid'])})
                    progress += 1

        for movie in movie_data:
            if movie['imdbid']:
                movie['status'] = 'Disabled'
                movie['predb'] = 'found'
                movie['finished_file'] = movie['path']
                movie['origin'] = 'Directory Import'
                response = json.loads(self.add_wanted_movie(json.dumps(movie), full_metadata=True))
                if response['response'] is True:
                    fake_results.append(searchresults.generate_simulacrum(movie))
                    yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                    progress += 1
                    success.append(movie)
                    continue
                else:
                    yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': response['error']})
                    progress += 1
                    continue
            else:
                logging.error('Unable to find {} on TMDB.'.format(movie['imdbid']))
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': 'IMDB ID invalid or missing.'})
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

        current_dir = current_dir.strip()
        move_dir = move_dir.strip()

        response = {}

        new_path = os.path.normpath(os.path.join(current_dir, move_dir))
        response['new_path'] = new_path

        try:
            response['list'] = [i for i in os.listdir(new_path) if os.path.isdir(os.path.join(new_path, i)) and not i.startswith('.')]
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
            except Exception as e:  # noqa
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
    def import_kodi_movies(self, movies):
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
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': 'Unable to find {} on TMDB.'.format(movie['imdbid'])})
                progress += 1
                continue

            movie['id'] = tmdb_data['id']
            movie['size'] = 0
            movie['status'] = 'Disabled'
            movie['predb'] = 'found'
            movie['finished_file'] = movie.get('finished_file', '').strip()
            movie['origin'] = 'Kodi Import'

            response = json.loads(self.add_wanted_movie(json.dumps(movie)))
            if response['response'] is True:
                fake_results.append(searchresults.generate_simulacrum(movie))
                yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                progress += 1
                success.append(movie)
                continue
            else:
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': response['error']})
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

    import_kodi_movies._cp_config = {'response.stream': True}

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
        except Exception as e:  # noqa
            logging.error('Unable to prase Plex CSV', exc_info=True)
            return

        if csv_text:
            return json.dumps(library.ImportPlexLibrary.read_csv(csv_text))
        else:
            return json.dumps()

    @cherrypy.expose
    def import_plex_csv(self, movies, corrected_movies):
        ''' Imports list of movies genrated by csv import
        movie_data: list of dicts of movie info ready to import
        corrected_movies: list of dicts of user-corrected movie info

        Iterates through corrected_movies and attmpts to get metadata again if required.

        If imported, generates and stores fake search result.

        Creates dict {'success': [], 'failed': []} and
            appends movie data to the appropriate list.

        Yeilds generator object of json objects
        '''

        movie_data = json.loads(movies)
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
                    yield json.dumps({'response': False, 'movie': data, 'progress': [progress, length], 'error': 'Unable to find {} on TMDB.'.format(data['imdbid'])})
                    progress += 1

        for movie in movie_data:
            if movie['imdbid']:
                movie['status'] = 'Disabled'
                movie['predb'] = 'found'
                movie['origin'] = 'Plex Import'

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
                    yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': response['error']})
                    progress += 1
                    continue
            else:
                logging.error('Unable to find {} on TMDB.'.format(movie['imdbid']))
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': 'IMDB ID invalid or missing.'})
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

    import_plex_csv._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cp_movies(self, url, apikey):

        url = '{}/api/{}/movie.list/'.format(url, apikey)

        if not url.startswith('http'):
            url = 'http://{}'.format(url)

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
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': response['error']})
                progress += 1
                continue

        for movie in finished:
            movie['predb'] = 'found'
            movie['status'] = 'Disabled'
            movie['origin'] = 'CouchPotato Import'

            response = json.loads(self.add_wanted_movie(json.dumps(movie), full_metadata=True))
            if response['response'] is True:
                fake_results.append(searchresults.generate_simulacrum(movie))
                yield json.dumps({'response': True, 'progress': [progress, length], 'movie': movie})
                progress += 1
                success.append(movie)
                continue
            else:
                yield json.dumps({'response': False, 'movie': movie, 'progress': [progress, length], 'error': response['error']})
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
    def manager_backlog_search(self, movies):
        '''
        movies: list of dict of movies, must contain keys imdbid and tmdbid
        '''

        '''
        if backlog_movies:
            logging.debug('Backlog movies: {}'.format(backlog_movies))
            for movie in backlog_movies:
                imdbid = movie['imdbid']
                title = movie['title']
                year = movie['year']
                quality = movie['quality']

                logging.info('Performing backlog search for {} {}.'.format(title, year))
                self.search(imdbid, title, year, quality)
                continue
        '''

        movies = json.loads(movies)
        ids = [i['imdbid'] for i in movies]

        movies = [i for i in self.sql.get_user_movies() if i['imdbid'] in ids]

        for i, movie in enumerate(movies):
            title = movie['title']
            year = movie['year']
            imdbid = movie['imdbid']
            year = movie['year']
            quality = movie['quality']

            logging.info("Performing backlog search for {} {}.".format(title, year))

            if not self.searcher.search(imdbid, title, year, quality):
                response = {'response': False, 'error': 'Unable to access database.', 'imdbid': imdbid, "index": i + 1}
            else:
                response = {'response': True, "index": i + 1}

            yield json.dumps(response)

    manager_backlog_search._cp_config = {'response.stream': True}

    @cherrypy.expose
    def manager_update_metadata(self, movies):
        '''
        movies: list of dict of movies, must contain keys imdbid and tmdbid
        '''
        movies = json.loads(movies)
        for i, movie in enumerate(movies):
            r = json.loads(self.update_metadata(movie['imdbid'], tmdbid=movie['tmdbid']))

            if r['response'] is False:
                response = {'response': False, 'error': r['error'], 'imdbid': movie['imdbid'], "index": i + 1}
            else:
                response = {'response': True, "index": i + 1}

            yield json.dumps(response)

    manager_update_metadata._cp_config = {'response.stream': True}

    @cherrypy.expose
    def manager_change_quality(self, movies, quality):
        '''
        movies: list of dict of movies, must contain keys imdbid
        quality: str quality to set movies to
        '''
        movies = json.loads(movies)
        for i, movie in enumerate(movies):
            r = json.loads(self.change_quality_profile(json.dumps({'Default': quality}), imdbid=movie['imdbid']))
            if r['response'] is False:
                response = {'response': False, 'error': r['error'], 'imdbid': movie['imdbid'], "index": i + 1}
            else:
                response = {'response': True, "index": i + 1}

            yield json.dumps(response)

    manager_change_quality._cp_config = {'response.stream': True}

    @cherrypy.expose
    def manager_reset_movies(self, movies):
        movies = json.loads(movies)

        for i, movie in enumerate(movies):
            imdbid = movie['imdbid']
            if not self.sql.purge_search_results(imdbid):
                yield json.dumps({'response': False, 'error': 'Unable to purge search results.', 'imdbid': imdbid, "index": i + 1})
                continue

            db_reset = {'quality': 'Default',
                        'status': 'Waiting',
                        'finished_date': None,
                        'finished_score': None,
                        'backlog': 0,
                        'finished_file': None
                        }

            if not self.sql.update_multiple('MOVIES', db_reset, imdbid=imdbid):
                yield json.dumps({'response': False, 'error': 'Unable to update database.', 'imdbid': imdbid, "index": i + 1})
                continue

            yield json.dumps({'response': True, "index": i + 1})

    manager_reset_movies._cp_config = {'response.stream': True}

    @cherrypy.expose
    def manager_remove_movies(self, movies):
        movies = json.loads(movies)

        for i, movie in enumerate(movies):
            r = json.loads(self.remove_movie(movie['imdbid']))

            if r['response'] is False:
                response = {'response': False, 'error': r['error'], 'imdbid': movie['imdbid'], "index": i + 1}
            else:
                response = {'response': True, "index": i + 1}

            yield(json.dumps(response))

    manager_remove_movies._cp_config = {'response.stream': True}

    @cherrypy.expose
    def generate_stats(self):
        return json.dumps(self.manage.get_stats())

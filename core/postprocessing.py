import datetime
import json
import logging
import os
import re
import shutil

import cherrypy
import core
from core import plugins, movieinfo, snatcher, sqldb, updatestatus, ajax
from core.library import Metadata

logging = logging.getLogger(__name__)


class Postprocessing(object):
    exposed = True

    def __init__(self):
        self.tmdb = movieinfo.TMDB()
        self.plugins = plugins.Plugins()
        self.sql = sqldb.SQL()
        self.ajax = ajax.Ajax()
        self.snatcher = snatcher.Snatcher()
        self.update = updatestatus.Status()
        self.metadata = Metadata()

    def null(*args, **kwargs): return

    @cherrypy.expose
    def POST(self, **data):
        ''' Handles post-processing requests.
        :kwparam **dara: keyword params send through POST request URL

        required kw params:
            apikey: str Watcher api key
            mode: str post-processing mode (complete, failed)
            guid: str download link of file. Can be url or magnet link.
            path: str path to downloaded files. Can be single file or dir

        optional kw params:
            imdbid: str imdb identification number (tt123456)
            downloadid: str id number from downloader

        Returns str json.dumps(dict) to post-process reqesting application.
        '''

        config = core.CONFIG['Postprocessing']

        logging.info('#################################')
        logging.info('Post-processing request received.')
        logging.info('#################################')

        # check for required keys
        for key in ['apikey', 'mode', 'guid', 'path']:
            if key not in data:
                logging.warning('Missing key {}'.format(key))
                return json.dumps({'response': 'false',
                                  'error': 'missing key: {}'.format(key)})

        # check if api key is correct
        if data['apikey'] != core.CONFIG['Server']['apikey']:
            logging.warning('Incorrect API key.'.format(key))
            return json.dumps({'response': 'false',
                              'error': 'incorrect api key'})

        # check if mode is valid
        if data['mode'] not in ['failed', 'complete']:
            logging.warning('Invalid mode value: {}.'.format(data['mode']))
            return json.dumps({'response': 'false',
                              'error': 'invalid mode value'})

        # modify path based on remote mapping
        data['path'] = self.map_remote(data['path'])

        # get the actual movie file name
        data['movie_file'] = self.get_movie_file(data['path'])

        if data['movie_file']:
            logging.info('Parsing release name for information.')
            data.update(self.metadata.parse_filename(data['movie_file']))

        # Get possible local data or get TMDB data to merge with self.params.
        logging.info('Gathering release information.')
        data.update(self.get_movie_info(data))

        # remove any invalid characters
        for k, v in data.items():
            # but we have to keep the path unmodified
            repl = config['replaceillegal']
            if k != 'path' and k != 'movie_file' and type(v) == str:
                data[k] = re.sub(r'[:"*?<>|]+', repl, v)

        # At this point we have all of the information we're going to get.
        if data['mode'] == 'failed':
            logging.warning('Post-processing as Failed.')
            response = self.failed(data)
            logging.warning(response)
        elif data['mode'] == 'complete':
            logging.info('Post-processing as Complete.')

            response = self.complete(data)

            response['data'].pop('backlog', '')
            response['data'].pop('predb', '')
            response['data'].pop('source', '')

            title = response['data'].get('title')
            year = response['data'].get('year')
            imdbid = response['data'].get('imdbid')
            resolution = response['data'].get('resolution')
            rated = response['data'].get('rated')
            original_file = response['data'].get('original_file')
            finished_file = response['data'].get('finished_file')
            downloadid = response['data'].get('downloadid')
            finished_date = response['data'].get('finished_date')
            quality = response['data'].get('quality')

            self.plugins.finished(title, year, imdbid, resolution, rated, original_file, finished_file, downloadid, finished_date, quality)

            logging.info(response)
        else:
            logging.warning('Invalid mode value: {}.'.format(data['mode']))
            return json.dumps({'response': 'false',
                               'error': 'invalid mode value'}, indent=2, sort_keys=True)

        logging.info('#################################')
        logging.info('Post-processing complete.')
        logging.info(json.dumps(response, indent=2, sort_keys=True))
        logging.info('#################################')

        return json.dumps(response, indent=2, sort_keys=True)

    def get_movie_file(self, path):
        ''' Looks for the filename of the movie being processed
        :param path: str url-passed path to download dir

        If path is a file, just returns path.
        If path is a directory, finds the largest file in that dir.

        Returns str absolute path /home/user/filename.ext
        '''

        logging.info('Finding movie file.')
        if os.path.isfile(path):
            return path
        else:
            # Find the biggest file in the dir. Assume that this is the movie.
            try:
                files = os.listdir(path)
            except Exception as e: # noqa
                logging.error('Path not found in filesystem. Will be unable to move or rename.',
                              exc_info=True)
                return ''

            files = []
            for root, dirs, filenames in os.walk(path):
                for file in filenames:
                    files.append(os.path.join(root, file))

            if files == []:
                return ''

            biggestfile = None
            s = 0
            for file in files:
                size = os.path.getsize(file)
                if size > s:
                    biggestfile = file
                    s = size

            logging.info('Post-processing file {}.'.format(biggestfile))

            return biggestfile

    def get_movie_info(self, data):
        ''' Gets score, imdbid, and other information to help process
        :param data: dict url-passed params with any additional info

        Uses guid to look up local details.
        If that fails, uses downloadid.
        If that fails, searches tmdb for imdbid

        If everything fails returns empty dict {}

        Returns dict of any gathered information
        '''

        # try to get searchresult using guid first then downloadid
        logging.info('Searching local database for guid.')
        result = self.sql.get_single_search_result('guid', data['guid'])
        if not result:
            logging.info('Guid not found.')
            if 'downloadid' in data.keys():
                # try to get result from downloadid
                logging.info('Searching local database for downloadid.')
                result = self.sql.get_single_search_result('downloadid', data['downloadid'])
                if result:
                    logging.info('Searchresult found by downloadid.')
                    if result['guid'] != data['guid']:
                        logging.info('Guid for downloadid does not match local data. '
                                     'Adding guid2 to processing data.')
                        data['guid2'] = result['guid']
        else:
            logging.info('Searchresult found by guid.')

        # if we found it, get local movie info
        if result:
            logging.info('Searching local database by imdbid.')
            data = self.sql.get_movie_details('imdbid', result['imdbid'])
            if data:
                logging.info('Movie data found locally by imdbid.')
                data['finished_score'] = result['score']
                data['resolution'] = result['resolution']
                data['downloadid'] = result['downloadid']
            else:
                logging.info('Unable to find movie in local db.')

        # Still no luck? Try to get the info from TMDB
        else:
            logging.info('Unable to find local data for release. Attempting to get info from file.')
            data.update(self.metadata.get_metadata(data['movie_file']))

        if data:
            if not data.get('quality'):
                data['quality'] = 'Default'
            return data
        else:
            return {}

    def failed(self, data):
        ''' Post-process failed downloads.
        :param data: dict of gathered data from downloader and localdb/tmdb

        In SEARCHRESULTS marks guid as Bad
        In MARKEDRESULTS:
            Creates or updates entry for guid and optional guid2 with status=Bad
        Updates MOVIES status

        If Clean Up is enabled will delete path and contents.
        If Auto Grab is enabled will grab next best release.

        Returns dict of post-processing results
        '''

        config = core.CONFIG['Postprocessing']

        # dict we will json.dump and send back to downloader
        result = {}
        result['status'] = 'finished'
        result['data'] = data
        result['tasks'] = {}

        # mark guid in both results tables
        logging.info('Marking guid as Bad.')
        guid_result = {'url': data['guid']}

        if data['guid']:  # guid can be empty string
            if self.update.searchresults(data['guid'], 'Bad'):
                guid_result['update_SEARCHRESULTS'] = 'true'
            else:
                guid_result['update_SEARCHRESULTS'] = 'false'

            if self.update.markedresults(data['guid'], 'Bad', imdbid=data['imdbid']):
                guid_result['update_MARKEDRESULTS'] = 'true'
            else:
                guid_result['update_MARKEDRESULTS'] = 'false'

        # create result entry for guid
        result['tasks']['guid'] = guid_result

        # if we have a guid2, do it all again
        if 'guid2' in data.keys():
            logging.info('Marking guid2 as Bad.')
            guid2_result = {'url': data['guid2']}
            if self.update.searchresults(data['guid2'], 'Bad'):
                guid2_result['update SEARCHRESULTS'] = 'true'
            else:
                guid2_result['update SEARCHRESULTS'] = 'false'

            if self.update.markedresults(data['guid2'], 'Bad', imdbid=data['imdbid'], ):
                guid2_result['update_MARKEDRESULTS'] = 'true'
            else:
                guid2_result['update_MARKEDRESULTS'] = 'false'
            # create result entry for guid2
            result['tasks']['guid2'] = guid2_result

        # set movie status
        if data['imdbid']:
            logging.info('Setting MOVIE status.')
            r = str(self.update.movie_status(data['imdbid'])).lower()
        else:
            logging.info('Imdbid not supplied or found, unable to update Movie status.')
            r = 'false'
        result['tasks']['update_movie_status'] = r

        # delete failed files
        if config['cleanupfailed']:
            result['tasks']['cleanup'] = {'enabled': 'true', 'path': data['path']}

            logging.info('Deleting leftover files from failed download.')
            if self.cleanup(data['path']) is True:
                result['tasks']['cleanup']['response'] = 'true'
            else:
                result['tasks']['cleanup']['response'] = 'false'
        else:
            result['tasks']['cleanup'] = {'enabled': 'false'}

        # grab the next best release
        if core.CONFIG['Search']['autograb']:
            result['tasks']['autograb'] = {'enabled': 'true'}
            logging.info('Grabbing the next best release.')
            if data.get('imdbid') and data.get('quality'):
                if self.snatcher.auto_grab(data):
                    r = 'true'
                else:
                    r = 'false'
            else:
                r = 'false'
            result['tasks']['autograb']['response'] = r
        else:
            result['tasks']['autograb'] = {'enabled': 'false'}

        # all done!
        result['status'] = 'finished'
        return result

    def complete(self, data):
        '''
        :param data: str guid of downloads
        :param downloadid: str watcher-generated downloadid
        :param path: str path to downloaded files.

        All params can be blank strings ie ""

        In SEARCHRESULTS marks guid as Finished
        In MARKEDRESULTS:
            Creates or updates entry for guid and optional guid with status=bad
        In MOVIES updates finished_score and finished_date
        Updates MOVIES status

        Checks to see if we found a movie file. If not, ends here.

        If Renamer is enabled, renames movie file according to core.CONFIG
        If Mover is enabled, moves file to location in core.CONFIG, then...
            If Clean Up enabled, deletes path after Mover finishes.
            Clean Up will not execute without Mover success.

        Returns dict of post-processing results
        '''
        config = core.CONFIG['Postprocessing']

        # dict we will json.dump and send back to downloader
        result = {}
        result['status'] = 'incomplete'
        result['data'] = data
        result['data']['finished_date'] = str(datetime.date.today())
        result['tasks'] = {}

        # mark guid in both results tables
        logging.info('Marking guid as Finished.')
        guid_result = {}
        if data['guid'] and data.get('imdbid'):
            if self.update.searchresults(data['guid'], 'Finished', movie_info=data):
                guid_result['update_SEARCHRESULTS'] = 'true'
            else:
                guid_result['update_SEARCHRESULTS'] = 'false'

            if self.update.markedresults(data['guid'], 'Finished', imdbid=data['imdbid']):
                guid_result['update_MARKEDRESULTS'] = 'true'
            else:
                guid_result['update_MARKEDRESULTS'] = 'false'

            # create result entry for guid
            result['tasks'][data['guid']] = guid_result

        # if we have a guid2, do it all again
        if 'guid2' in data.keys() and data.get('imdbid'):
            logging.info('Marking guid2 as Finished.')
            guid2_result = {}
            if self.update.searchresults(data['guid2'], 'Finished', movie_info=data):
                guid2_result['update_SEARCHRESULTS'] = 'true'
            else:
                guid2_result['update_SEARCHRESULTS'] = 'false'

            if self.update.markedresults(data['guid2'], 'Finished', imdbid=data['imdbid'],
                                         ):
                guid2_result['update_MARKEDRESULTS'] = 'true'
            else:
                guid2_result['update_MARKEDRESULTS'] = 'false'

            # create result entry for guid2
            result['tasks'][data['guid2']] = guid2_result

        # set movie status and add finished date/score
        if data.get('imdbid'):
            if not self.sql.row_exists('MOVIES', imdbid=data['imdbid']):
                logging.info('{} not found in library, adding now.'.format(data.get('title')))
                data['status'] = 'Disabled'
                self.ajax.add_wanted_movie(json.dumps(data))

            logging.info('Setting MOVIE status.')
            r = str(self.update.movie_status(data['imdbid'])).lower()
            self.sql.update('MOVIES', 'finished_date', result['data']['finished_date'], 'imdbid', data['imdbid'])
            self.sql.update('MOVIES', 'finished_score', result['data'].get('finished_score'), 'imdbid', data['imdbid'])
        else:
            logging.info('Imdbid not supplied or found, unable to update Movie status.')
            r = 'false'
        result['tasks']['update_movie_status'] = r

        # renamer
        if config['renamerenabled']:
            result['tasks']['renamer'] = {'enabled': 'true'}
            result['data']['original_file'] = result['data']['movie_file']
            response = self.renamer(data)
            if response is None:
                result['tasks']['renamer']['response'] = 'false'
            else:
                path = os.path.split(data['movie_file'])[0]
                data['movie_file'] = os.path.join(path, response)
                result['tasks']['renamer']['response'] = 'true'
        else:
            logging.info('Renamer disabled.')
            result['tasks']['mover'] = {'enabled': 'false'}

        # mover
        if config['moverenabled']:
            result['tasks']['mover'] = {'enabled': 'true'}
            response = self.mover(data)
            if response is False:
                result['tasks']['mover']['response'] = 'false'
            else:
                data['finished_file'] = response
                result['tasks']['mover']['response'] = 'true'
        else:
            logging.info('Mover disabled.')
            result['tasks']['mover'] = {'enabled': 'false'}

        if data.get('imdbid'):
            self.sql.update('MOVIES', 'finished_file', result['data'].get('finished_file'), 'imdbid', data['imdbid'])

        # Delete leftover dir. Skip if createhardlinks enabled or if mover disabled/failed
        if config['cleanupenabled']:
            result['tasks']['cleanup'] = {'enabled': 'true'}

            if config['createhardlink']:
                logging.info('Hardlink creation enabled. Skipping Cleanup.')
                result['tasks']['cleanup']['response'] = 'skipped'
                return result

            # fail if mover disabled or failed
            if config['moverenabled'] is False or \
                    result['tasks']['mover']['response'] == 'false':
                logging.info('Mover either disabled or failed. Skipping Cleanup.')
                result['tasks']['cleanup']['response'] = 'false'
            else:
                if self.cleanup(data['path']):
                    r = 'true'
                else:
                    r = 'false'
                result['tasks']['cleanup']['response'] = r
        else:
            result['tasks']['cleanup'] = {'enabled': 'false'}

        # all done!
        result['status'] = 'finished'
        return result

    def map_remote(self, path):
        ''' Alters directory based on remote mappings settings
        path: str path from download client

        Replaces the base of the file tree with the 'local' mapping.
            Ie, '/home/user/downloads/Watcher' becomes '//server/downloads/Watcher'

        'path' can be file or directory, it doesn't matter.

        If more than one match is found, defaults to the longest path.
            remote: local = '/home/users/downloads/': '//server/downloads/'
                            '/home/users/downloads/Watcher/': '//server/downloads/Watcher/'
            In this case, a supplied remote '/home/users/downloads/Watcher/' will match a
            startswith() for both supplied settings. So we will default to the longest path.
        Returns str new path
        '''

        maps = core.CONFIG['Postprocessing']['RemoteMapping']

        matches = []
        for remote in maps.keys():
            if path.startswith(remote):
                matches.append(remote)
        if not matches:
            return path
        else:
            match = max(matches, key=len)
            new_path = path.replace(match, maps[match])
            logging.info('Changing remote path from {} to {}'.format(path, new_path))
            return new_path

    def compile_path(self, string, data):
        ''' Compiles string to file/path names
        :param string: str brace-formatted string to substitue values
        :data data: dict of values to sub into string

        Takes a renamer/mover path and adds values.
            ie '{title} {year} {resolution}' -> 'Movie 2017 1080P'
        Subs double spaces. Trims trailing spaces. Removes any invalid characters.

        Can return blank string ''

        Sends string to self.sanitize() to remove illegal characters

        Returns str new path
        '''
        new_string = string
        for k, v in data.items():
            k = "{"+k+"}"
            if k in new_string:
                new_string = new_string.replace(k, v)

        while '  ' in new_string:
            new_string = new_string.replace('  ', ' ')

        while len(string) > 1 and new_string[-1] == ' ':
            new_string = new_string[:-1]

        new_string = self.map_remote(new_string)

        logging.debug('Created path {} from {}'.format(new_string, string))

        return self.sanitize(new_string)

    def renamer(self, data):
        ''' Renames movie file based on renamerstring.
        :param data: dict of movie information.

        Renames movie file based on params in core.CONFIG

        Returns str new file name or None on failure
        '''

        config = core.CONFIG['Postprocessing']

        renamer_string = config['renamerstring']

        # check to see if we have a valid renamerstring
        if re.match(r'{(.*?)}', renamer_string) is None:
            logging.info('Invalid renamer string {}'.format(renamer_string))
            return None

        # existing absolute path
        abs_path_old = data['movie_file']
        file_path = os.path.split(data['movie_file'])[0]

        # get the extension
        ext = os.path.splitext(abs_path_old)[1]

        # get the new file name
        new_name = self.compile_path(renamer_string, data)

        if not new_name:
            logging.info('New file name would be blank. Cancelling renamer.')
            return None

        if core.CONFIG['Postprocessing']['replacespaces']:
            new_name = new_name.replace(' ', '.')
        new_name = new_name + ext

        # new absolute path
        abs_path_new = os.path.join(file_path, new_name)

        logging.info('Renaming {} to {}'.format(os.path.basename(data['movie_file']), new_name))
        try:
            os.rename(abs_path_old, abs_path_new)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Renamer failed: Could not rename file.', exc_info=True)
            return None

        # return the new name so the mover knows what our file is
        return new_name

    def recycle(self, recycle_bin, abs_filepath):
        file_dir, file_name = os.path.split(abs_filepath)
        if not os.path.isdir(recycle_bin):
            logging.info('Creating recycle bin direcotry {}'.format(recycle_bin))
            try:
                os.makedirs(recycle_bin)
            except Exception as e:
                logging.error('Recycling failed: Could not create Recycle Bin directory {}.'.format(recycle_bin), exc_info=True)
                return False
        logging.info('Recycling {} to recycle bin {}'.format(abs_filepath, recycle_bin))
        try:
            if os.path.isfile(os.path.join(recycle_bin, file_name)):
                os.remove(os.path.join(recycle_bin, file_name))
            shutil.copystat = self.null
            shutil.move(abs_filepath, recycle_bin)
            return True
        except Exception as e: # noqa
            logging.error('Recycling failed: Could not move file.', exc_info=True)
            return False

    def remove_additional_files(self, movie_file):
        ''' Removes addtional associated file of movie_file
        movie_file: str absolute file path of old movie file

        Removes any file in movie_file's directory that share the same file name

        Does not cause mover failure on error.
        Returns bool
        '''

        logging.info('Removing additional files for {}'.format(movie_file))

        path, file_name = os.path.split(movie_file)

        fname = os.path.splitext(file_name)[0]

        for i in os.listdir(path):
            if os.path.splitext(i)[0] == fname:
                logging.info('Removing additional file {}'.format(i))
                try:
                    os.remove(os.path.join(path, i))
                except Exception as e: #noqa
                    logging.warning('Unable to remove {}'.format(i), exc_info=True)
        return

    def mover(self, data):
        '''Moves movie file to path constructed by moverstring
        :param data: dict of movie information.

        Moves file to location specified in core.CONFIG

        If target file already exists either:
            Delete it prior to copying new file in (since os.rename in windows doesn't overwrite)
                OR:
            Create Recycle Bin directory (if neccesary) and move the old file there.

        Copies and renames additional files

        Returns str new file location or False on failure
        '''

        config = core.CONFIG['Postprocessing']
        recycle_bin = self.compile_path(config['recyclebindirectory'], data)
        target_folder = os.path.normpath(self.compile_path(config['moverpath'], data))
        target_folder = os.path.join(target_folder, '')

        # if the new folder doesn't exist, make it
        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
        except Exception as e:
            logging.error('Mover failed: Could not create directory {}.'.format(target_folder), exc_info=True)
            return False

        current_file_path = data['movie_file']
        current_path, file_name = os.path.split(current_file_path)
        # If finished_file exists, recycle or remove
        if data.get('finished_file'):
            old_movie = data['finished_file']
            logging.info('Checking if old file {} exists.'.format(old_movie))
            if os.path.isfile(old_movie):

                if config['recyclebinenabled']:
                    logging.info('Old movie file found, recycling.')
                    if not self.recycle(recycle_bin, old_movie):
                        return False
                else:
                    logging.info('Deleting old file {}'.format(old_movie))
                    try:
                        os.remove(old_movie)
                    except Exception as e:
                        logging.error('Mover failed: Could not delete file.', exc_info=True)
                        return False
                if config['removeadditionalfiles']:
                    self.remove_additional_files(old_movie)
        # Check if the target file name exists in target dir, recycle or remove
        if os.path.isfile(os.path.join(target_folder, file_name)):
            existing_movie_file = os.path.join(target_folder, file_name)
            logging.info('Existing file {} found in {}'.format(file_name, target_folder))
            if config['recyclebinenabled']:
                if not self.recycle(recycle_bin, existing_movie_file):
                    return False
            else:
                logging.info('Deleting old file {}'.format(existing_movie_file))
                try:
                    os.remove(existing_movie_file)
                except Exception as e:
                    logging.error('Mover failed: Could not delete file.', exc_info=True)
                    return False
            if config['removeadditionalfiles']:
                self.remove_additional_files(existing_movie_file)
        # Now to actually move the new Movie
        logging.info('Moving {} to {}'.format(current_file_path, target_folder))
        try:
            shutil.copystat = self.null
            shutil.move(current_file_path, target_folder)
        except Exception as e: # noqa
            logging.error('Mover failed: Could not move file.', exc_info=True)
            return False

        new_file_location = os.path.join(target_folder, os.path.basename(data['movie_file']))

        # Create hardlink

        if config['createhardlink']:
            logging.info('Creating hardlink from {} to {}.'.format(new_file_location, data['original_file']))
            os.link(new_file_location, data['original_file'])

        logging.info('Copying and renaming any extra files.')

        moveextensions = config['moveextensions']
        keep_extentions = [i for i in moveextensions.split(',') if i != '']

        renamer_string = config['renamerstring']
        new_name = self.compile_path(renamer_string, data)

        for root, dirs, filenames in os.walk(data['path']):
            for name in filenames:
                old_abs_path = os.path.join(root, name)
                ext = os.path.splitext(old_abs_path)[1]  # '.ext'

                target_file = '{}{}'.format(os.path.join(target_folder, new_name), ext)

                if ext.replace('.', '') in keep_extentions:
                    append = 0
                    while os.path.isfile(target_file):
                        append += 1
                        new_filename = '{}({})'.format(new_name, str(append))
                        target_file = '{}{}'.format(os.path.join(target_folder, new_filename), ext)
                    try:
                        logging.info('Moving {} to {}'.format(old_abs_path, target_file))
                        shutil.copyfile(old_abs_path, target_file)
                    except Exception as e: # noqa
                        logging.error('Mover failed: Could not copy {}.'.format(old_abs_path), exc_info=True)
        return new_file_location

    def cleanup(self, path):
        ''' Deletes specified path
        :param path: str of path to remover

        path can be file or dir

        Returns Bool on success/failure
        '''

        # if its a dir
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                return True
            except Exception as e:
                logging.error('Could not delete path.', exc_info=True)
                return False
        elif os.path.isfile(path):
            # if its a file
            try:
                os.remove(path)
                return True
            except Exception as e: # noqa
                logging.error('Could not delete path.', exc_info=True)
                return False
        else:
            # if it is somehow neither
            return False

    def sanitize(self, string):
        config = core.CONFIG['Postprocessing']
        repl = config['replaceillegal']

        string = re.sub(r'["*?<>|]+', repl, string)

        drive, path = os.path.splitdrive(string)
        path = path.replace(':', repl)
        return ''.join([drive, path])

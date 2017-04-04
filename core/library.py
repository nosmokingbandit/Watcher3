import os
import json
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from core.movieinfo import TMDB
from core import sqldb
from core.helpers import Url
import PTN
import datetime
import logging
import uuid
import xml.etree.cElementTree as ET
import csv

logging = logging.getLogger(__name__)

sql = sqldb.SQL()


class ImportDirectory(object):

    def __init__(self):
        return

    @staticmethod
    def scan_dir(directory, minsize=500, recursive=True):
        ''' Scans directory for movie files
        directory: str base directory of movie library
        minsize: int minimum filesize in MB <default 500>
        recursive: bool scan recursively or just root directory <default True>

        Returns list of files
        '''

        logging.info('Scanning {} for movies.'.format(directory))

        files = []
        try:
            if recursive:
                files = ImportDirectory._walk(directory)
            else:
                files = [os.path.join(directory, i) for i in os.listdir(directory) if os.path.isfile(os.path.join(directory, i))]
        except Exception as e:
            return {'error': str(e)}

        files = [i for i in files if os.path.getsize(i) >= (minsize * 1024**2)]

        return {'files': files}

    @staticmethod
    def _walk(directory):
        ''' Recursively gets all files in dir
        dir: directory to scan for files

        Returns list of absolute file paths
        '''

        files = []
        dir_contents = os.listdir(directory)
        for i in dir_contents:
            logging.info('Scanning {}{}{}'.format(directory, os.sep, i))
            full_path = os.path.join(directory, i)
            if os.path.isdir(full_path):
                files = files + ImportDirectory._walk(full_path)
            else:
                files.append(full_path)
        return files


class ImportKodiLibrary(object):

    @staticmethod
    def get_movies(url):
        ''' Gets list of movies from kodi server
        url: str url of kodi server

        url should include auth info if required.

        Gets movies from kodi, reformats list, and adds resolution/source info.
        Since Kodi doesn't care about souce we default to BluRay-<resolution>

        Returns list of dicts of movies
        '''

        krequest = {"jsonrpc": "2.0",
                    "method": "VideoLibrary.GetMovies",
                    "params": {
                        "filter": {
                            "field": "playcount",
                            "operator": "is",
                            "value": "0"
                        },
                        "limits": {
                            "start": 0,
                            "end": 0
                        },
                        "properties": [
                            "title",
                            "year",
                            "imdbnumber",
                            "file",
                            "streamdetails"
                        ],
                        "sort": {
                            "order": "ascending",
                            "method": "label",
                            "ignorearticle": True
                        }
                    },
                    "id": "libMovies"
                    }

        logging.info('Retreiving movies from Kodi.')
        url = '{}/jsonrpc?request={}'.format(url, json.dumps(krequest))

        try:
            response = Url.open(url)
        except Exception as e:
            logging.error('Unable to reach Kodi server.', exc_info=True)
            return {'response': False, 'error': str(e.args[0].reason).split(']')[-1]}

        if response.status_code != 200:
            if response.status_code == 401:
                return {'response': False, 'error': 'Incorrect credentials.'}
            elif response.status_code == 403:
                return {'response': False, 'error': 'Unauthorized credentials.'}
            elif response.status_code == 404:
                return {'response': False, 'error': 'Server not found.'}
            else:
                return {'response': False, 'error': 'Error {}'.format(response.status_code)}

        library = [i['imdbid'] for i in sql.get_user_movies()]
        movies = []

        today = str(datetime.date.today())
        for i in json.loads(response.text)['result']['movies']:
            if i['imdbnumber'] in library:
                logging.info('{} in library, skipping.'.format(i['imdbidnumber']))
                continue

            movie = {}
            movie['title'] = i['title']
            movie['year'] = i['year']
            movie['imdbid'] = i['imdbnumber']
            movie['file'] = i['file']
            movie['added_date'] = movie['finished_date'] = today
            movie['audiocodec'] = i['streamdetails']['audio'][0].get('codec')
            if movie['audiocodec'] == 'dca' or movie['audiocodec'].startswith('dts'):
                movie['audiocodec'] = 'DTS'
            movie['videocodec'] = i['streamdetails']['video'][0].get('codec')
            width = i['streamdetails']['video'][0]['width']
            if width > 1920:
                movie['resolution'] = 'BluRay-4K'
            elif 1920 >= width > 1440:
                movie['resolution'] = 'BluRay-1080P'
            elif 1440 >= width > 720:
                movie['resolution'] = 'BluRay-720P'
            else:
                movie['resolution'] = 'DVD-SD'

            movies.append(movie)

        return {'response': True, 'movies': movies}


class ImportPlexLibrary(object):

    @staticmethod
    def get_libraries(url, token):
        ''' Gets list of libraries in server url
        url: url and port of plex server
        token: plex auth token for server

        Returns list of dicts
        '''

        headers = {'X-Plex-Token': token}

        url = '{}/library/sections'.format(url)

        try:
            r = Url.open(url, headers=headers)
            xml = r.text
        except Exception as e: #noqa
            logging.error('Unable to contact Plex server.', exc_info=True)
            return {'response', False, 'error', 'Unable to contact Plex server.'}

        libs = []
        try:
            root = ET.fromstring(xml)

            for directory in root.findall('Directory'):
                lib = directory.attrib
                lib['path'] = directory.find('Location').attrib['path']
                libs.append(lib)
        except Exception as e: #noqa
            logging.error('Unable to parse Plex xml.', exc_info=True)
            return {'response', False, 'error', 'Unable to parse Plex xml.'}

        return {'response': True, 'libraries': libs}

    @staticmethod
    def get_movies(server, libid, token):

        headers = {'X-Plex-Token': token}
        url = '{}/library/sections/{}/all'.format(server, libid)

        try:
            r = Url.open(url, headers=headers)
            xml = r.text
        except Exception as e: #noqa
            logging.error('Unable to contact Plex server.', exc_info=True)
            return {'response', False, 'error', 'Unable to contact Plex server.'}

        movies = []
        try:
            root = ET.fromstring(xml)

            for i in root:
                movie = {}

                movies.append(movie)

        except Exception as e: #noqa
            logging.error('Unable to parse Plex xml.', exc_info=True)
            return {'response', False, 'error', 'Unable to parse Plex xml.'}

        return {'response': True, 'movies': movies}

    @staticmethod
    def get_token(username=None, password=None):
        ''' Gets auth token for plex
        username: str username of plex account
        password: str password of plex account

        Returns str token or None
        '''

        plex_url = 'https://plex.tv/users/sign_in.json'
        post_data = {'user[login]': username,
                     'user[password]': password
                     }
        headers = {'X-Plex-Client-Identifier': str(uuid.getnode()),
                   'X-Plex-Product': 'Watcher',
                   'X-Plex-Version': '1.0'}

        try:
            r = Url.open(plex_url, post_data=post_data, headers=headers)
            return json.loads(r.text)['user'].get('authentication_token')
        except Exception as e: #noqa
            logging.error('Unable to get Plex token.', exc_info=True)
            return None

    @staticmethod
    def read_csv(csv_text):
        library = [i['imdbid'] for i in sql.get_user_movies()]
        try:
            movies = []
            reader = csv.DictReader(csv_text.splitlines())
            for row in reader:
                movies.append(dict(row))
        except Exception as e: #noqa
            return {'response': False, 'error': e}

        parsed_movies = []
        incomplete = []
        today = str(datetime.date.today())
        for movie in movies:
            complete = True
            parsed = {}

            db_id = movie['MetaDB Link'].split('/')[-1]
            if db_id.startswith('tt'):
                if db_id in library:
                    continue
                else:
                    parsed['imdbid'] = db_id
            elif all(i.isdigit() for i in db_id):
                parsed['tmdbid'] = db_id
            else:
                complete = False

            parsed['title'] = movie['Title']
            parsed['year'] = movie['Year']

            parsed['added_date'] = parsed['finished_date'] = today

            parsed['audiocodec'] = movie['Audio Codec']
            if parsed['audiocodec'] == 'dca' or parsed['audiocodec'].startswith('dts'):
                parsed['audiocodec'] = 'DTS'

            width = int(movie['Width'])
            if width > 1920:
                parsed['resolution'] = 'BluRay-4K'
            elif 1920 >= width > 1440:
                parsed['resolution'] = 'BluRay-1080P'
            elif 1440 >= width > 720:
                parsed['resolution'] = 'BluRay-720P'
            else:
                parsed['resolution'] = 'DVD-SD'

            parsed['size'] = int(movie['Part Size as Bytes'])
            parsed['file'] = movie['Part File']

            if complete:
                parsed_movies.append(parsed)
            else:
                incomplete.append(parsed)

        return {'response': True, 'movies': parsed_movies, 'incomplete': incomplete}


class Metadata(object):

    def __init__(self):
        self.tmdb = TMDB()
        return

    def get_metadata(self, filepath):
        ''' Gets video metadata using hachoir.parser
        filepath: str absolute path to movie file

        On failure can return empty dict

        Returns dict
        '''

        logging.info('Gathering metadata for {}.'.format(filepath))

        data = {
            'title': '',
            'year': '',
            'resolution': '',
            'releasegroup': '',
            'audiocodec': '',
            'videocodec': '',
            'source': '',
            'imdbid': '',
            'size': '',
            'path': filepath
            }

        titledata = self.parse_filename(filepath)
        data.update(titledata)

        filedata = self.parse_media(filepath)
        data.update(filedata)

        if data.get('resolution'):
            if data['resolution'].upper() in ['4K', '1080P', '720P']:
                data['resolution'] = '{}-{}'.format(data['source'] or 'BluRay', data['resolution'].upper())
            else:
                data['resolution'] = 'DVD-SD'

        if data.get('title') and not data.get('imdbid'):
            tmdbdata = self.tmdb.search('{} {}'.format(data['title'], data.get('year', '')), single=True)
            if tmdbdata:
                data['year'] = tmdbdata['release_date'][:4]
                data.update(tmdbdata)
                data['imdbid'] = self.tmdb.get_imdbid(data['id'])
            else:
                logging.warning('Unable to get data from TMDB for {}'.format(data['imdbid']))
                return data

        return data

    def parse_media(self, filepath):
        ''' Uses Hachoir-metadata to parse the file header to metadata
        filepath: str absolute path to file

        Attempts to get resolution from media width

        Returns dict of metadata
        '''

        metadata = {}
        try:
            with createParser(filepath) as parser:
                extractor = extractMetadata(parser)
            filedata = extractor.exportDictionary(human=False)
            parser.stream._input.close()

        except Exception as e: #noqa
            logging.error('Unable to parse metadata from file header.', exc_info=True)
            return metadata

        if filedata:
            if filedata.get('Metadata'):
                width = filedata['Metadata'].get('width')
            elif metadata.get('video[1]'):
                width = filedata['video[1]'].get('width')
            else:
                width = None

            if width:
                width = int(width)
                if width > 1920:
                    filedata['resolution'] = '4K'
                elif 1920 >= width > 1440:
                    filedata['resolution'] = '1080P'
                elif 1440 >= width > 720:
                    filedata['resolution'] = '720P'
                else:
                    filedata['resolution'] = 'SD'

            if filedata.get('audio[1]'):
                metadata['audiocodec'] = filedata['audio[1]'].get('compression').replace('A_', '')
            if filedata.get('video[1]'):
                metadata['videocodec'] = filedata['video[1]'].get('compression').split('/')[0].replace('V_', '')

        return metadata

    def parse_filename(self, filepath):
        ''' Uses PTN to get as much info as possible from path
        filepath: str absolute path to file

        Returns dict of Metadata
        '''
        logging.info('Parsing {} for movie information.'.format(filepath))

        # This is our base dict. Contains all neccesary keys, though they can all be empty if not found.
        metadata = {
            'title': '',
            'year': '',
            'resolution': '',
            'releasegroup': '',
            'audiocodec': '',
            'videocodec': '',
            'source': '',
            'imdbid': ''
            }

        titledata = PTN.parse(os.path.basename(filepath))
        # this key is useless
        if 'excess' in titledata:
            titledata.pop('excess')

        if len(titledata) < 2:
            logging.info('Parsing filename doesn\'t look accurate. Parsing parent folder name.')

            path_list = os.path.split(filepath)[0].split(os.sep)
            titledata = PTN.parse(path_list[-1])
            logging.info('Found {} in parent folder.'.format(titledata))
        else:
            logging.info('Found {} in filename.'.format(titledata))

        title = titledata.get('title')
        if title and title[-1] == '.':
            titledata['title'] = title[:-1]

        # Make sure this matches our key names
        if 'codec' in titledata:
            titledata['videocodec'] = titledata.pop('codec')
        if 'audio' in titledata:
            titledata['audiocodec'] = titledata.pop('audio')
        if 'quality' in titledata:
            titledata['source'] = titledata.pop('quality')
        if 'group' in titledata:
            titledata['releasegroup'] = titledata.pop('group')
        metadata.update(titledata)

        return metadata

    def convert_to_db(self, movie):
        ''' Takes movie data and converts to a database-writable dict
        movie: dict of movie information

        Used to prepare TMDB's movie response for write into MOVIES
        Must include Watcher-specific keys ie resolution,
        Makes sure all keys match and are present.
        Sorts out alternative titles and digital release dates

        Returns dict ready to sql.write into MOVIES
        '''

        if not movie.get('imdbid'):
            movie['imdbid'] = 'N/A'

        if movie.get('release_date'):
            movie['year'] = movie['release_date'][:4]
        else:
            movie['year'] = 'N/A'

        if movie.get('added_date') is None:
            movie['added_date'] = str(datetime.date.today())

        movie['poster'] = 'images/poster/{}.jpg'.format(movie['imdbid'])
        movie['plot'] = movie['overview']
        movie['url'] = 'https://www.themoviedb.org/movie/{}'.format(movie['id'])
        movie['score'] = movie['vote_average']
        if movie.get('status') != 'Disabled':
            movie['status'] = 'Wanted'
        movie['added_date'] = str(datetime.date.today())
        movie['backlog'] = 0
        movie['tmdbid'] = movie['id']

        a_t = []
        for i in movie['alternative_titles']['titles']:
            if i['iso_3166_1'] == 'US':
                a_t.append(i['title'])

        movie['alternative_titles'] = ','.join(a_t)

        dates = []
        for i in movie['release_dates']['results']:
            for d in i['release_dates']:
                if d['type'] == 4:
                    dates.append(d['release_date'])

        if dates:
            movie['digital_release_date'] = max(dates)[:10]

        if movie.get('quality') is None:
            movie['quality'] = 'Default'

        movie['finished_file'] = movie.get('finished_file')

        required_keys = ('added_date', 'alternative_titles', 'digital_release_date', 'imdbid', 'tmdbid', 'title', 'year', 'poster', 'plot', 'url', 'score', 'release_date', 'rated', 'status', 'quality', 'addeddate', 'backlog', 'finished_file', 'finished_date')

        movie = {k: v for k, v in movie.items() if k in required_keys}

        return movie

import os

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from core.movieinfo import TMDB
from core import sqldb
import PTN
import datetime
import logging

logging = logging.getLogger(__name__)


class ImportDirectory(object):

    def __init__(self):
        self.tmdb = TMDB()
        self.sql = sqldb.SQL()
        return

    def scan_dir(self, directory, minsize=500, recursive=True):
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
                files = self._walk(directory)
            else:
                files = [os.path.join(directory, i) for i in os.listdir(directory) if os.path.isfile(os.path.join(directory, i))]
        except Exception as e:
            return {'error': str(e)}

        files = [i for i in files if os.path.getsize(i) >= (minsize * 1024**2)]

        return {'files': files}

    def fake_search_result(self, movie):
        ''' Generated fake search result for imported movies
        movie: dict of movie info

        Resturns dict to match SEARCHRESULTS table
        '''

        result = {'status': 'Finished',
                  'info_link': '#',
                  'pubdate': None,
                  'title': None,
                  'imdbid': movie['imdbid'],
                  'torrentfile': None,
                  'indexer': 'Library Import',
                  'date_found': str(datetime.date.today()),
                  'score': None,
                  'type': 'import',
                  'downloadid': None,
                  'guid': None,
                  'resolution': movie.get('resolution'),
                  'size': movie.get('size', '')
                  }

        title = '{}.{}.{}.{}.{}.{}.{}'.format(movie['title'],
                                              movie['year'],
                                              result['resolution'],
                                              movie['source'],
                                              movie['audiocodec'],
                                              movie['videocodec'],
                                              movie['releasegroup']
                                              )

        while len(title) > 0 and title[-1] == '.':
            title = title[:-1]

        while '..' in title:
            title = title.replace('..', '.')

        result['title'] = title

        result['guid'] = movie.get('guid') or 'IMPORT{}'.format(title.encode("hex").zfill(16)[:16])

        return result

    def _walk(self, directory):
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
                files = files + self._walk(full_path)
            else:
                files.append(full_path)
        return files


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

        logging.info('Gathering metada for {}.'.format(filepath))

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

        Used to prepare movie data for write into MOVIES
        Makes sure all keys match and are present.
        Sorts out alternative titles and digital release dates

        Returns dict ready to sql.write into MOVIES
        '''

        if not movie.get('imdbid'):
            movie['imdbid'] = movie.pop('imdb_id')

        if movie.get('release_date'):
            movie['year'] = movie['release_date'][:4]
        else:
            movie['year'] = 'N/A'

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

        dates = [None]
        for i in movie['release_dates']['results']:
            for d in i['release_dates']:
                if d['type'] == 4:
                    dates.append(d['release_date'])

        digital_date = max(dates)
        if digital_date:
            movie['digital_release_date'] = digital_date[:10]

        if movie.get('quality') is None:
            movie['quality'] = 'Default'

        required_keys = ('added_date', 'alternative_titles', 'digital_release_date', 'imdbid', 'tmdbid', 'title', 'year', 'poster', 'plot', 'url', 'score', 'release_date', 'rated', 'status', 'quality', 'addeddate', 'backlog')

        movie = {k: v for k, v in movie.items() if k in required_keys}

        return movie

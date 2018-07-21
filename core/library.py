import os
import json
import datetime
import logging
import csv
import threading
from core import searchresults, plugins
import core
from core.movieinfo import TheMovieDatabase, Poster
from core.helpers import Url
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import PTN
from gettext import gettext as _


logging = logging.getLogger(__name__)


class ImportDirectory(object):

    @staticmethod
    def scan_dir(directory, minsize=500, recursive=True):
        ''' Scans directory for movie files
        directory (str): absolute path to base directory of movie library
        minsize (int): minimum filesize in MB                       <optional - default 500>
        recursive (bool): scan recursively or just root directory   <optional - default True>

        Checks mimetype for video type

        Returns dict ajax-style response
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

        f = []
        logging.debug('Specified minimum file size: {} Bytes.'.format(minsize * 1024**2))
        ms = minsize * 1024**2
        for i in files:
            s = os.path.getsize(i)
            if not s >= (ms):
                logging.debug('{} size is {} skipping.'.format(i, s))
                continue
            f.append(i)
        return {'files': f}

    @staticmethod
    def _walk(directory):
        ''' Recursively gets all files in dir
        directory: directory to scan for files

        Returns list of absolute file paths
        '''

        files = []
        dir_contents = os.listdir(directory)
        for i in dir_contents:
            full_path = os.path.join(directory, i)
            if os.path.isdir(full_path):
                logging.debug('Scanning {}{}{}'.format(directory, os.sep, i))
                files = files + ImportDirectory._walk(full_path)
            else:
                logging.debug('Found file {}'.format(full_path))
                files.append(full_path)
        return files


class ImportKodiLibrary(object):

    @staticmethod
    def get_movies(url):
        ''' Gets list of movies from kodi server
        url (str): url of kodi server

        url should include auth info if required.

        Gets movies from kodi, reformats list, and adds resolution/source info.
        Since Kodi doesn't care about souce we default to BluRay-<resolution>

        Returns dict ajax-style response
        '''

        krequest = {'jsonrpc': '2.0',
                    'method': 'VideoLibrary.GetMovies',
                    'params': {
                        'limits': {
                            'start': 0,
                            'end': 0
                        },
                        'properties': [
                            'title',
                            'year',
                            'imdbnumber',
                            'file',
                            'streamdetails'
                        ],
                        'sort': {
                            'order': 'ascending',
                            'method': 'label',
                            'ignorearticle': True
                        }
                    },
                    'id': 'libMovies'
                    }

        logging.info('Retreiving movies from Kodi.')
        url = '{}/jsonrpc?request={}'.format(url, json.dumps(krequest))

        try:
            response = Url.open(url)
        except Exception as e:
            logging.error('Unable to reach Kodi server.', exc_info=True)
            return {'response': False, 'error': str(e.args[0].reason).split(']')[-1]}

        if response.status_code != 200:
            return {'response': False, 'error': '{} {}'.format(response.status_code, response.reason.title())}

        library = [i['imdbid'] for i in core.sql.get_user_movies()]
        movies = []

        today = str(datetime.date.today())
        for i in json.loads(response.text)['result']['movies']:

            if i['imdbnumber'] in library:
                logging.info('{} in library, skipping.'.format(i['imdbnumber']))
                continue

            logging.info('Found Kodi movie {}.'.format(i['title']))

            movie = {}
            movie['title'] = i['title']
            movie['year'] = i['year']
            movie['imdbid'] = i['imdbnumber']
            movie['file'] = i['file']
            movie['added_date'] = movie['finished_date'] = today
            movie['audiocodec'] = i['streamdetails']['audio'][0].get('codec') if i['streamdetails']['audio'] else ''
            if movie['audiocodec'] == 'dca' or movie['audiocodec'].startswith('dts'):
                movie['audiocodec'] = 'DTS'
            movie['resolution'] = 'Unknown'
            if i['streamdetails']['video']:
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
            else:
                movie['videocodec'] = ''

            movies.append(movie)

        return {'response': True, 'movies': movies}


class ImportPlexLibrary(object):
    ''' Several of these methods are not currently used due to Plex's
    api being less than ideal.
    '''

    @staticmethod
    def read_csv(csv_text):
        ''' Parse plex csv
        csv_text (str): text from csv file

        Returns dict ajax-style response
        '''
        logging.info('Parsing Plex library CSV.')

        library = [i['imdbid'] for i in core.sql.get_user_movies()]
        library_tmdb = [i['tmdbid'] for i in core.sql.get_user_movies()]

        delim = csv_text.split('"')[2]
        if delim not in (',', ';', '|', ':', '\t'):
            delim = ','

        try:
            movies = []
            reader = csv.DictReader(csv_text.splitlines(), delimiter=delim)
            for row in reader:
                movies.append(dict(row))
        except Exception as e:
            return {'response': False, 'error': str(e)}

        parsed_movies = []
        incomplete = []
        today = str(datetime.date.today())

        for movie in movies:
            parsed = {}
            try:
                logging.info('Parsing Plex movie {}'.format(movie['Title']))
                complete = True
                db_id = movie['MetaDB Link'].split('/')[-1]
                if db_id.startswith('tt'):
                    if db_id in library:
                        continue
                    else:
                        parsed['imdbid'] = db_id
                elif db_id.isdigit():
                    if db_id in library_tmdb:
                        continue
                    else:
                        parsed['tmdbid'] = db_id
                else:
                    parsed['imdbid'] = ''
                    complete = False

                parsed['title'] = movie['Title']
                parsed['year'] = movie['Year']

                parsed['added_date'] = parsed['finished_date'] = today

                parsed['audiocodec'] = movie['Audio Codec']
                if parsed['audiocodec'] == 'dca' or parsed['audiocodec'].startswith('dts'):
                    parsed['audiocodec'] = 'DTS'

                w = movie['Width']
                pw = ''
                while len(w) > 0 and w[0].isdigit():
                    pw += w[0]
                    w = w[1:]

                if pw:
                    width = int(pw)
                else:
                    width = 0
                    complete = False
                if width > 1920:
                    parsed['resolution'] = 'BluRay-4K'
                elif 1920 >= width > 1440:
                    parsed['resolution'] = 'BluRay-1080P'
                elif 1440 >= width > 720:
                    parsed['resolution'] = 'BluRay-720P'
                else:
                    parsed['resolution'] = 'DVD-SD'

                s = movie['Part Size as Bytes']
                ps = ''
                while len(s) > 0 and s[0].isdigit():
                    ps += s[0]
                    s = s[1:]

                parsed['size'] = int(ps) if ps else 0
                parsed['file'] = movie['Part File']

                if complete:
                    parsed_movies.append(parsed)
                else:
                    incomplete.append(parsed)
            except Exception as e:
                logging.error('Error parsing Plex CSV.', exc_info=True)
                incomplete.append(parsed)

        return {'response': True, 'complete': parsed_movies, 'incomplete': incomplete}


class ImportCPLibrary(object):

    @staticmethod
    def get_movies(url):
        ''' Gets list of movies from CP
        url (str): full url of cp movies.list api call

        Returns dict ajax-style response
        '''

        logging.info('Reading CouchPotato library.')

        try:
            r = Url.open(url)
        except Exception as e:
            return {'response': False, 'error': str(e)}
        if r.status_code != 200:
            return {'response': False, 'error': '{} {}'.format(r.status_code, r.reason.title())}
        try:
            cp = json.loads(r.text)
        except Exception as e:
            return {'response': False, 'error': _('Malformed json response from CouchPotato')}

        if cp['total'] == 0:
            return ['']

        library = [i['imdbid'] for i in core.sql.get_user_movies()]
        movies = []
        for m in cp['movies']:
            if m['info']['imdb'] in library:
                logging.debug('{} in library, skipping.'.format(m['info']['original_title']))
                continue
            logging.debug('Parsing CouchPotato movie {}'.format(m['info']['original_title']))
            movie = {}
            if m['status'] == 'done':
                movie['status'] = 'Disabled'
                for i in m['releases']:
                    if i['status'] == 'done':
                        if i.get('info'):
                            name = i['info']['name'].lower()
                        elif i.get('identifier'):
                            name = i['identifier'].lower()
                        else:
                            continue
                        title_data = PTN.parse(name)

                        movie['audiocodec'] = title_data.get('audio')
                        movie['videocodec'] = title_data.get('codec')

                        movie['size'] = i.get('info', {}).get('size', 0) * 1024 * 1024
                        if any(i in name for i in ['4K', 'UHD', '2160P']):
                            movie['resolution'] = 'BluRay-4K'
                        elif any(i in name for i in ['1080', 'brrip', 'bdrip', 'bluray']):
                            movie['resolution'] = 'BluRay-1080P'
                        elif '720' in name:
                            movie['resolution'] = 'BluRay-720P'
                        else:
                            movie['resolution'] = 'DVD-SD'
                        break

                movie.setdefault('size', 0)
                movie['quality'] = 'Default'
            else:
                movie['status'] = 'Waiting'

            movie.setdefault('resolution', 'BluRay-1080P')

            cpm = m['info']

            movie['title'] = cpm.get('original_title') or ''
            movie['year'] = cpm.get('year') or 'N/A'
            movie['overview'] = cpm.get('plot') or ''
            p = (cpm.get('images', {}).get('poster_original') or [''])[0].split('/')[-1]
            if p:
                movie['poster_path'] = p
            else:
                movie['poster_path'] = None

            movie['url'] = 'https://www.themoviedb.org/movie/{}'.format(cpm.get('tmdb_id', ''))
            movie['vote_average'] = cpm.get('rating', {}).get('imdb', [0])[0]
            movie['imdbid'] = cpm.get('imdb')
            movie['id'] = cpm.get('tmdb_id')
            ts = cpm.get('release_date', {}).get('theater')
            movie['release_date'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else None

            movie['alternative_titles'] = {'titles': [{'iso_3166_1': 'US',
                                                       'title': ','.join(cpm.get('titles', []))
                                                       }]
                                           }
            movie['release_dates'] = {'results': []}

            movies.append(movie)

        return {'response': True, 'movies': movies}


class Metadata(object):
    ''' Methods for gathering/preparing metadata for movies
    '''

    @staticmethod
    def from_file(filepath, imdbid=None):
        ''' Gets video metadata using hachoir.parser
        filepath (str): absolute path to movie file
        imdbid (str): imdb id #             <optional - Default None>

        On failure can return empty dict

        Returns dict
        '''

        logging.info('Gathering metadata for {}.'.format(filepath))

        data = {
            'title': None,
            'year': None,
            'resolution': None,
            'rated': None,
            'imdbid': imdbid,
            'videocodec': None,
            'audiocodec': None,
            'releasegroup': None,
            'source': None,
            'quality': None,
            'path': filepath,
            'edition': []
        }

        titledata = Metadata.parse_filename(filepath)
        data.update(titledata)

        filedata = Metadata.parse_media(filepath)
        data.update(filedata)

        if data.get('resolution'):
            if data['resolution'].upper() in ('4K', '1080P', '720P'):
                data['resolution'] = '{}-{}'.format(data['source'] or 'BluRay', data['resolution'].upper())
            else:
                data['resolution'] = 'DVD-SD'

        if data.get('title') and not data.get('imdbid'):
            title_date = '{} {}'.format(data['title'], data['year']) if data.get('year') else data['title']
            tmdbdata = TheMovieDatabase.search(title_date, single=True)
            if not tmdbdata:
                logging.warning('Unable to get data from TheMovieDB for {}'.format(data['title']))
                return data

            tmdbdata = tmdbdata[0]
            tmdbid = tmdbdata.get('id')

            if not tmdbid:
                logging.warning('Unable to get data from TheMovieDB for {}'.format(data['imdbid']))
                return data

            tmdbdata = tmdbdata = TheMovieDatabase._search_tmdbid(tmdbid)
            if tmdbdata:
                tmdbdata = tmdbdata[0]
            else:
                logging.warning('Unable to get data from TMDB for {}'.format(data['imdbid']))
                return data

            data['year'] = tmdbdata['release_date'][:4]
            data.update(tmdbdata)

        if data.get('3d'):
            data['edition'].append('3D')

        data['edition'] = ' '.join(sorted(data['edition']))

        return data

    @staticmethod
    def parse_media(filepath):
        ''' Uses Hachoir-metadata to parse the file header to metadata
        filepath (str): absolute path to file

        Attempts to get resolution from media width

        Returns dict of metadata
        '''

        logging.info('Parsing codec data from file {}.'.format(filepath))
        metadata = {}
        try:
            with createParser(filepath) as parser:
                extractor = extractMetadata(parser)
            filedata = extractor.exportDictionary(human=False)
            parser.stream._input.close()

        except Exception as e:
            logging.error('Unable to parse metadata from file header.', exc_info=True)
            return metadata

        if filedata:
            # For mp4, mvk, avi in order
            video = filedata.get('Metadata') or \
                filedata.get('video[1]') or \
                filedata.get('video') or \
                {}

            # mp4 doesn't have audio data so this is just for mkv and avi
            audio = filedata.get('audio[1]') or {}

            if video.get('width'):
                width = int(video.get('width'))
                if width > 1920:
                    metadata['resolution'] = '4K'
                elif 1920 >= width > 1440:
                    metadata['resolution'] = '1080P'
                elif 1440 >= width > 720:
                    metadata['resolution'] = '720P'
                else:
                    metadata['resolution'] = 'SD'
            else:
                metadata['resolution'] = 'SD'

            if audio.get('compression'):
                metadata['audiocodec'] = audio['compression'].replace('A_', '')
            if video.get('compression'):
                metadata['videocodec'] = video['compression'].split('/')[0].split('(')[0].replace('V_', '')

        return metadata

    @staticmethod
    def parse_filename(filepath):
        ''' Uses PTN to get as much info as possible from path
        filepath (str): absolute path to movie file

        Parses parent directory name first, then file name if folder name seems incomplete.

        Returns dict of metadata
        '''

        dirname = os.path.split(filepath)[0].split(os.sep)[-1]

        logging.info('Parsing directory name for movie information: {}.'.format(dirname))

        meta_data = PTN.parse(dirname)
        for i in ('excess', 'episode', 'episodeName', 'season', 'garbage', 'website'):
            meta_data.pop(i, None)

        if len(meta_data) > 3:
            meta_data['release_name'] = dirname
            logging.info('Found {} in filename.'.format(meta_data))
        else:
            logging.debug('Parsing directory name does not look accurate. Parsing file name.')
            filename = os.path.basename(filepath)
            meta_data = PTN.parse(filename)
            logging.info('Found {} in file name.'.format(meta_data))
            if len(meta_data) < 2:
                logging.warning('Little information found in file name. Movie may be incomplete.')
            meta_data['release_title'] = filename

        title = meta_data.get('title')
        if title and title[-1] == '.':
            meta_data['title'] = title[:-1]

        # Make sure this matches our key names
        if 'year' in meta_data:
            meta_data['year'] = str(meta_data['year'])
        meta_data['videocodec'] = meta_data.pop('codec', None)
        meta_data['audiocodec'] = meta_data.pop('audio', None)

        qual = meta_data.pop('quality', '')
        for source, aliases in core.CONFIG['Quality']['Aliases'].items():
            if any(a.lower() == qual.lower() for a in aliases):
                meta_data['source'] = source
                break
        meta_data.setdefault('source', None)

        meta_data['releasegroup'] = meta_data.pop('group', None)

        return meta_data

    @staticmethod
    def convert_to_db(movie):
        ''' Takes movie data and converts to a database-writable dict
        movie (dict): of movie information

        Used to prepare TMDB's movie response for write into MOVIES
        Must include Watcher-specific keys ie resolution
        Makes sure all keys match and are present
        Sorts out alternative titles and digital release dates

        Returns dict ready to sql.write into MOVIES
        '''

        logging.info('Converting movie metadata to database structure for {}.'.format(movie['title']))

        if not movie.get('imdbid'):
            movie['imdbid'] = 'N/A'

        if not movie.get('year') and movie.get('release_date'):
            movie['year'] = movie['release_date'][:4]
        elif not movie.get('year'):
            movie['year'] = 'N/A'

        movie.setdefault('added_date', str(datetime.date.today()))

        if movie.get('poster_path'):
            movie['poster'] = '{}.jpg'.format(movie['imdbid'])
        else:
            movie['poster'] = None

        movie['plot'] = movie.get('overview') if not movie.get('plot') else movie.get('plot')
        movie['url'] = 'https://www.themoviedb.org/movie/{}'.format(movie.get('id', movie.get('tmdbid')))
        movie['score'] = movie.get('score') or movie.get('vote_average') or 0

        if not movie.get('status'):
            movie['status'] = 'Waiting'
        movie['backlog'] = 0
        if not movie.get('tmdbid'):
            movie['tmdbid'] = movie.get('id')

        if not isinstance(movie.get('alternative_titles'), str):
            a_t = []
            for i in movie.get('alternative_titles', {}).get('titles', []):
                if i['iso_3166_1'] == 'US':
                    a_t.append(i['title'])

            movie['alternative_titles'] = ','.join(a_t)

        dates = []
        for i in movie.get('release_dates', {}).get('results', []):
            for d in i['release_dates']:
                if d['type'] > 4:
                    dates.append(d['release_date'])

        if dates:
            movie['media_release_date'] = min(dates)[:10]

        if not movie.get('quality'):
            movie['quality'] = 'Default'

        movie['finished_file'] = movie.get('finished_file')

        if movie['title'].startswith('The '):
            movie['sort_title'] = movie['title'][4:] + ', The'
        elif movie['title'].startswith('A '):
            movie['sort_title'] = movie['title'][2:] + ', A'
        elif movie['title'].startswith('An '):
            movie['sort_title'] = movie['title'][3:] + ', An'
        else:
            movie['sort_title'] = movie['title']

        if not movie.get('filters'):
            movie['filters'] = '{"preferredwords": "", "requiredwords": "", "ignoredwords": ""}'

        for k, v in movie.items():
            if isinstance(v, str):
                movie[k] = v.strip()

        movie = {k: v for k, v in movie.items() if k in [i.name for i in core.sql.MOVIES.c]}

        return movie

    @staticmethod
    def update(imdbid, tmdbid=None, force_poster=True):
        ''' Updates metadata from TMDB
        imdbid (str): imdb id #
        tmdbid (str): or int tmdb id #                                  <optional - default None>
        force_poster (bool): whether or not to always redownload poster <optional - default True>

        If tmdbid is None, looks in database for tmdbid using imdbid.
        If that fails, looks on tmdb api for imdbid
        If that fails returns error message

        If force_poster is True, the poster will be re-downloaded.
        If force_poster is False, the poster will only be redownloaded if the local
            database does not have a 'poster' filepath stored. In other words, this
            will only grab missing posters.

        Returns dict ajax-style response
        '''

        logging.info('Updating metadata for {}'.format(imdbid))
        movie = core.sql.get_movie_details('imdbid', imdbid)

        if force_poster:
            get_poster = True
        elif not movie.get('poster'):
            get_poster = True
        elif not os.path.isfile(os.path.join(core.PROG_PATH, movie['poster'])):
            get_poster = True
        else:
            logging.debug('Poster will not be redownloaded.')
            get_poster = False

        if tmdbid is None:
            tmdbid = movie.get('tmdbid')

            if not tmdbid:
                logging.debug('TMDB id not found in local database, searching TMDB for {}'.format(imdbid))
                tmdb_data = TheMovieDatabase._search_imdbid(imdbid)
                tmdbid = tmdb_data[0].get('id') if tmdb_data else None
            if not tmdbid:
                logging.debug('Unable to find {} on TMDB.'.format(imdbid))
                return {'response': False, 'error': 'Unable to find {} on TMDB.'.format(imdbid)}

        new_data = TheMovieDatabase._search_tmdbid(tmdbid)

        if not new_data:
            logging.warning('Empty response from TMDB.')
            return
        else:
            new_data = new_data[0]

        new_data.pop('status')

        target_poster = os.path.join(Poster.folder, '{}.jpg'.format(imdbid))

        if new_data.get('poster_path'):
            poster_path = 'http://image.tmdb.org/t/p/w300{}'.format(new_data['poster_path'])
            movie['poster'] = '{}.jpg'.format(movie['imdbid'])
        else:
            poster_path = None

        movie.update(new_data)
        movie = Metadata.convert_to_db(movie)

        core.sql.update_multiple_values('MOVIES', movie, 'imdbid', imdbid)

        if poster_path and get_poster:
            if os.path.isfile(target_poster):
                try:
                    os.remove(target_poster)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    logging.warning('Unable to remove existing poster.', exc_info=True)
                    return {'response': False, 'error': 'Unable to remove existing poster.'}

            Poster.save(imdbid, poster_path)

        return {'response': True, 'message': 'Metadata updated.'}


class Manage(object):
    ''' Methods to manipulate status of movies or search results in database
    '''

    @staticmethod
    def scanmissingfiles():
        movies = core.sql.execute(['SELECT * FROM MOVIES WHERE finished_file is not null'])

        if movies is None:
            logging.warning('Unable to read database.')
            return

        movies = core.sqldb.proxy_to_dict(movies)

        action = core.CONFIG['System']['FileManagement']['missingfileaction']
        db_update_values = []
        for i in movies:
            if not os.path.exists(i['finished_file']):
                logging.info('File {} is missing for movie {}'.format(i['finished_file'], i['title']))

                if action == 'remove':
                    if Manage.remove_movie(i['imdbid'])['response'] is False:
                        logging.error('Unable to remove {} from library'.format(i['title']))
                elif action == 'revert':
                    db_update_values.append({'imdbid': i['imdbid'],
                                             'finished_file': None,
                                             'finished_date': None,
                                             'status': 'Wanted',
                                             'backlog': 0})

                    if core.sql.delete('MARKEDRESULTS', 'imdbid', i['imdbid']) is None or \
                       core.sql.delete('SEARCHRESULTS', 'imdbid', i['imdbid']) is None:
                        logging.warning('Unable to remove marked releases. Status change may be incorrect.')

        if len(db_update_values) > 0:
            core.sql.update_multiple_rows('MOVIES', db_update_values, 'imdbid')

        return

    @staticmethod
    def verify(movie, today=None):
        ''' Checks for verfied releases based on config
        movie (dict): movie info
        today (obj): datetime.datetime.today() object   <optional - default calls datetime.dateimte.today()>

        Checks (in order):
            If verify releases is enabled
            If movie has a theatrical release date
            If theatrical release date is older than skip weeks per user config
            If predb verification -- check predb
            If home media release verification - check if release is in the past

            If all enabled conditions fail, return False

        Returns Bool
        '''
        today = today or datetime.datetime.today()

        if core.CONFIG['Search']['verifyreleases'] == '':
            verified = True
        elif not movie.get('release_date'):
            logging.info('{} does not have a theatrical release date, skipping verification check as Unverified.'.format(movie['title']))
            verified = False
        elif core.CONFIG['Search']['verifyreleasesskip'] and datetime.datetime.strptime(movie['release_date'], '%Y-%m-%d') + datetime.timedelta(days=7 * core.CONFIG['Search']['verifyreleasesskipweeks']) < today:
            logging.info('{} is older than {}, skipping verification check as Verified.'.format(movie['title'], core.CONFIG['Search']['verifyreleasesskipweeks']))
            verified = True

        elif core.CONFIG['Search']['verifyreleases'] == 'predb':
            if movie.get('predb') == 'found':
                verified = True
            else:
                verified = False

        elif core.CONFIG['Search']['verifyreleases'] == 'mediareleasedate':
            if not movie.get('predb') and movie.get('predb_backlog'):
                logging.debug('Resetting predb backlog status for unfound movie {} {}'.format(movie['title'], movie['year']))
                core.sql.update('MOVIES', 'predb_backlog', None, 'imdbid', movie['imdbid'])
            if not movie.get('media_release_date'):
                logging.info('{} does not yet have a home media release date.'.format(movie['title']))
                verified = False
            else:
                media_release = datetime.datetime.strptime(movie['media_release_date'], '%Y-%m-%d')
                if media_release < today:
                    verified = True
                else:
                    verified = False
        else:
            verified = False

        if verified and movie['status'] == 'Waiting':
            logging.info('Verification criteria met for {} {}, setting status to Wanted'.format(movie['title'], movie['year']))
            core.sql.update('MOVIES', 'status', 'Wanted', 'imdbid', movie['imdbid'])
        elif not verified and movie['status'] not in ('Waiting', 'Disabled', 'Finished'):
            logging.info('Verified criteria not met for {} {}, resetting setting status to Waiting'.format(movie['title'], movie['year']))
            core.sql.update('MOVIES', 'status', 'Waiting', 'imdbid', movie['imdbid'])

        if verified:
            logging.info('{} passes verification checks, will include title in search.'.format(movie['title']))
        else:
            logging.info('{} does not pass verification checks, will ignore for now.'.format(movie['title']))

        return verified

    @staticmethod
    def add_movie(movie, full_metadata=False):
        ''' Adds movie to Wanted list.
        movie (dict): movie info to add to database.
        full_metadata (bool): if data is complete and ready for write

        movie MUST inlcude tmdb id as data['id']

        Writes data to MOVIES table.

        If full_metadata is False, searches tmdb for data['id'] and updates data
            full_metadata should only be True when passing movie as data pulled
            directly from a tmdbid search

        If Search on Add enabled,
            searches for movie immediately in separate thread.
            If Auto Grab enabled, will snatch movie if found.

        Returns dict ajax-style response
        '''

        logging.info('Adding {} to library.'.format(movie.get('title')))

        response = {}
        tmdbid = movie['id']

        if not full_metadata:
            logging.debug('More information needed, searching TheMovieDB for {}'.format(tmdbid))
            tmdb_data = TheMovieDatabase._search_tmdbid(tmdbid)
            if not tmdb_data:
                response['error'] = _('Unable to find {} on TMDB.').format(tmdbid)
                return response
            else:
                tmdb_data = tmdb_data[0]
            tmdb_data.pop('status')
            movie.update(tmdb_data)

        if core.sql.row_exists('MOVIES', imdbid=movie['imdbid']):
            logging.info('{} already exists in library.'.format(movie['title']))

            response['response'] = False

            response['error'] = _('{} already exists in library.').format(movie['title'])
            return response

        movie.setdefault('quality', 'Default')
        movie.setdefault('status', 'Waiting')
        movie.setdefault('origin', 'Search')

        poster_path = movie.get('poster_path')

        movie = Metadata.convert_to_db(movie)

        if not core.sql.write('MOVIES', movie):
            response['response'] = False
            response['error'] = _('Could not write to database.')
        else:
            if poster_path:
                poster_url = 'http://image.tmdb.org/t/p/w300/{}'.format(poster_path)
                threading.Thread(target=Poster.save, args=(movie['imdbid'], poster_url)).start()

            response['response'] = True
            response['message'] = _('{} {} added to library.').format(movie['title'], movie['year'])
            plugins.added(movie['title'], movie['year'], movie['imdbid'], movie['quality'])

        return response

    @staticmethod
    def remove_movie(imdbid):
        ''' Remove movie from library
        imdbid (str): imdb id #

        Calls core.sql.remove_movie and removes poster (in separate thread)

        Returns dict ajax-style response
        '''

        logging.info('Removing {} for library.'.format(imdbid))

        m = core.sql.get_movie_details('imdbid', imdbid)

        removed = core.sql.remove_movie(imdbid)

        if removed is True:
            response = {'response': True, 'message': _('{} removed from library.').format(m.get('title'))}
            threading.Thread(target=Poster.remove, args=(imdbid,)).start()
        elif removed is False:
            response = {'response': False, 'error': _('Unable to remove {}.').format(m.get('title'))}
        elif removed is None:
            response = {'response': False, 'error': _('{} does not exist in library.').format(imdbid)}

        return response

    # @todo move to searchresults module?
    @staticmethod
    def searchresults(guid, status, movie_info=None):
        ''' Marks searchresults status
        guid (str): download link guid
        status (str): status to set
        movie_info (dict): of movie metadata    <optional - default None>

        If guid is in SEARCHRESULTS table, marks it as status.

        If guid not in SEARCHRESULTS, uses movie_info to create a result.

        Returns bool
        '''

        TABLE = 'SEARCHRESULTS'

        logging.info('Marking guid {} as {}.'.format(guid.split('&')[0], status))

        if core.sql.row_exists(TABLE, guid=guid):

            # Mark bad in SEARCHRESULTS
            logging.info('Marking {} as {} in SEARCHRESULTS.'.format(guid.split('&')[0], status))
            if not core.sql.update(TABLE, 'status', status, 'guid', guid):
                logging.error('Setting SEARCHRESULTS status of {} to {} failed.'.format(guid.split('&')[0], status))
                return False
            else:
                logging.info('Successfully marked {} as {} in SEARCHRESULTS.'.format(guid.split('&')[0], status))
                return True
        else:
            logging.info('Guid {} not found in SEARCHRESULTS, attempting to create entry.'.format(guid.split('&')[0]))
            if movie_info is None:
                logging.warning('Movie metadata not supplied, unable to create SEARCHRESULTS entry.')
                return False
            search_result = searchresults.generate_simulacrum(movie_info)
            search_result['indexer'] = 'Post-Processing Import'
            if not search_result.get('title'):
                search_result['title'] = movie_info['title']
            search_result['size'] = os.path.getsize(movie_info.get('orig_filename') or '.')
            if not search_result['resolution']:
                search_result['resolution'] = 'Unknown'

            search_result = searchresults.score([search_result], imported=True)[0]

            required_keys = ('score', 'size', 'status', 'pubdate', 'title', 'imdbid', 'indexer', 'date_found', 'info_link', 'guid', 'torrentfile', 'resolution', 'type', 'downloadid', 'freeleech')

            search_result = {k: v for k, v in search_result.items() if k in required_keys}

            if core.sql.write('SEARCHRESULTS', search_result):
                return True
            else:
                return False

    @staticmethod
    def markedresults(guid, status, imdbid=None):
        ''' Marks markedresults status
        guid (str): download link guid
        status (str): status to set
        imdbid (str): imdb identification number    <optional - default None>

        If guid is in MARKEDRESULTS table, marks it as status.
        If guid not in MARKEDRSULTS table, created entry. Requires imdbid.

        Returns bool
        '''

        TABLE = 'MARKEDRESULTS'

        if core.sql.row_exists(TABLE, guid=guid):
            # Mark bad in MARKEDRESULTS
            logging.info('Marking {} as {} in MARKEDRESULTS.'.format(guid.split('&')[0], status))
            if not core.sql.update(TABLE, 'status', status, 'guid', guid):
                logging.info('Setting MARKEDRESULTS status of {} to {} failed.'.format(guid.split('&')[0], status))
                return False
            else:
                logging.info('Successfully marked {} as {} in MARKEDRESULTS.'.format(guid.split('&')[0], status))
                return True
        else:
            logging.info('Guid {} not found in MARKEDRESULTS, creating entry.'.format(guid.split('&')[0]))
            if imdbid:
                DB_STRING = {}
                DB_STRING['imdbid'] = imdbid
                DB_STRING['guid'] = guid
                DB_STRING['status'] = status
                if core.sql.write(TABLE, DB_STRING):
                    logging.info('Successfully created entry in MARKEDRESULTS for {}.'.format(guid.split('&')[0]))
                    return True
                else:
                    logging.error('Unable to create entry in MARKEDRESULTS for {}.'.format(guid.split('&')[0]))
                    return False
            else:
                logging.warning('Imdbid not supplied or found, unable to add entry to MARKEDRESULTS.')
                return False

    @staticmethod
    def movie_status(imdbid):
        ''' Updates Movie status.
        imdbid (str): imdb identification number (tt123456)

        Updates Movie status based on search results.
        Always sets the status to the highest possible level.

        Returns str new movie status
        '''

        logging.info('Determining appropriate status for movie {}.'.format(imdbid))

        movie = core.sql.get_movie_details('imdbid', imdbid)
        if movie:
            current_status = movie.get('status')
        else:
            return ''

        if current_status == 'Disabled':
            return 'Disabled'

        new_status = None

        t = []

        if core.CONFIG['Downloader']['Sources']['usenetenabled']:
            t.append('nzb')
        if core.CONFIG['Downloader']['Sources']['torrentenabled']:
            t += ['torrent', 'magnet']

        cmd = 'SELECT DISTINCT status FROM SEARCHRESULTS WHERE imdbid="{}" AND type IN ("import", "{}")'.format(imdbid, '", "'.join(t))

        try:
            result_status = [i['status'] for i in core.sql.execute([cmd]).fetchall()] or []
        except Exception as e:
            logging.warning('Unable to determine movie status.', exc_info=True)
            result_status = []

        if 'Finished' in result_status:
            new_status = 'Finished'
        elif 'Snatched' in result_status:
            new_status = 'Snatched'
        elif 'Available' in result_status:
            new_status = 'Found'
        else:
            new_status = 'Wanted' if Manage.verify(movie) else 'Waiting'

        logging.info('Setting MOVIES {} status to {}.'.format(imdbid, new_status))
        if core.sql.update('MOVIES', 'status', new_status, 'imdbid', imdbid):
            return new_status
        else:
            logging.error('Could not set {} to {}'.format(imdbid, new_status))
            return ''

    @staticmethod
    def get_stats():
        ''' Gets stats from database for graphing
        Formats data for use with Morris graphing library

        Returns dict
        '''

        logging.info('Generating library stats.')

        stats = {}

        status = {'Waiting': 0,
                  'Wanted': 0,
                  'Found': 0,
                  'Snatched': 0,
                  'Finished': 0
                  }

        qualities = {'Default': 0}
        for i in core.CONFIG['Quality']['Profiles']:
            if i == 'Default':
                continue
            qualities[i] = 0

        years = {}
        added_dates = {}
        scores = {}

        movies = core.sql.get_user_movies()

        if not movies:
            return {'error', 'Unable to read database'}

        for movie in movies:
            if movie['status'] == 'Disabled':
                status['Finished'] += 1
            else:
                status[movie['status']] += 1

            if movie['quality'].startswith('{'):
                qualities['Default'] += 1
            else:
                if movie['quality'] not in qualities:
                    qualities[movie['quality']] = 1
                else:
                    qualities[movie['quality']] += 1

            if movie['year'] not in years:
                years[movie['year']] = 1
            else:
                years[movie['year']] += 1

            if movie['added_date'][:-3] not in added_dates:
                added_dates[movie['added_date'][:-3]] = 1
            else:
                added_dates[movie['added_date'][:-3]] += 1

            score = round((float(movie['score']) * 2)) / 2
            if score not in scores:
                scores[score] = 1
            else:
                scores[score] += 1

        stats['status'] = [{'label': k, 'value': v} for k, v in status.items()]
        stats['qualities'] = [{'label': k, 'value': v} for k, v in qualities.items()]
        stats['years'] = sorted([{'year': k, 'value': v} for k, v in years.items()], key=lambda k: k['year'])
        stats['added_dates'] = sorted([{'added_date': k, 'value': v} for k, v in added_dates.items() if v is not None], key=lambda k: k['added_date'])
        stats['scores'] = sorted([{'score': k, 'value': v} for k, v in scores.items()], key=lambda k: k['score'])
        return stats

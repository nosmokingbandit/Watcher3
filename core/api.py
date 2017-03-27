import json
import logging
import threading

import core
from core import ajax, sqldb, poster

logging = logging.getLogger(__name__)

api_version = 2.0

''' API

All methods output a json object:
{'response': true}

A 'true' response indicates that the request was valid and returs useful data.
A 'false' response indicates that the request was invalid. This will always include an
    'error' key that describes the reason for the failure.

All successul method calls then append addition key:value pairs to the output json.


# METHODS

mode=liststatus:
    input: imdbid=tt1234567     <optional>
    if imdbid supplied:
        output: {'movie': {'key': 'value', 'key2', 'value2'} }
    if no imdbid supplied:
        output: {'movies': [{'key': 'value', 'key2', 'value2'}, {'key': 'value', 'key2', 'value2'}] }

mode=addmovie
    input: imdbid=tt1234567     Either this or tmdbid required
    input: tmdbid=123456        Either this or imdbid required
    input: quality=Default      <optional>
    output: {'message': 'MOVIE TITLE YEAR added to wanted list.'}

    If quality is not supplied, uses 'Default' profile.

mode=removemovie
    input: imdbid=tt1234567
    output: {'removed': 'tt1234567'}

mode=get_config
    output: JSON-formatted config. Basically just the config file.

mode=version
    output: {'version': '4fcdda1df1a4ff327c3219311578d703a288e598', 'api_version': 1.0}


# API Version
Methods added to the api will increase the version by X.1
Version 1.11 is greater than 1.9
It is safe to assume that these version increases will not break any api interactions

Changes to the output responses will increase the version to the next whole number 2.0
Major version changes can be expected to break api interactions

# VERSION HISTORY
1.0     First commit
1.1     Consistency in responses

2.0     Change to semantically correct json. Responses are now bools instead of str 'true'/'false'

'''


class API(object):
    '''
    A simple GET/POST api. Used for basic remote interactions.
    '''
    exposed = True

    def __init__(self):
        self.sql = sqldb.SQL()
        self.ajax = ajax.Ajax()
        self.poster = poster.Poster()
        return

    def GET(self, **params):
        ''' GET request handler to post-processing.
        Don't use this. It only exists for testing purposes. Sending a GET
            is much easier than POST when testing changes.
        '''

        serverkey = core.CONFIG['Server']['apikey']

        if 'apikey' not in params:
            logging.warning('API request failed, no key supplied.')
            return json.dumps({'response': False,
                               'error': 'no api key supplied'})

        # check for api key
        if serverkey != params['apikey']:
            logging.warning('Invalid API key in request: {}'.format(params['apikey']))
            return json.dumps({'response': False,
                               'error': 'incorrect api key'})

        # find what we are going to do
        if 'mode' not in params:
            return json.dumps({'response': False,
                               'error': 'no api mode specified'})

        if params['mode'] == 'liststatus':

            if 'imdbid' in params:
                return self.liststatus(imdbid=params['imdbid'])
            else:
                return self.liststatus()

        elif params['mode'] == 'addmovie':
            if 'imdbid' not in params and 'tmdbid' not in params:
                return json.dumps({'response': False,
                                   'error': 'no movie id supplied'})
            if params.get('imdbid') and params.get('tmdbid'):
                return json.dumps({'response': False,
                                   'error': 'multiple movie ids supplied'})
            else:
                quality = params.get('quality')
                if params.get('imdbid'):
                    return self.addmovie(imdbid=params['imdbid'], quality=quality)
                elif params.get('tmdbid'):
                    return self.addmovie(tmdbid=params['tmdbid'], quality=quality)
        elif params['mode'] == 'removemovie':
            if 'imdbid' not in params:
                return json.dumps({'response': False,
                                   'error': 'no imdbid supplied'})
            else:
                imdbid = params['imdbid']
            return self.removemovie(imdbid)

        elif params['mode'] == 'version':
            return self.version()

        elif params['mode'] == 'get_config':
            return json.dumps(core.CONFIG, sort_keys=True, indent=4)

        else:
            return json.dumps({'response': False,
                               'error': 'invalid mode'})

    def liststatus(self, imdbid=None):
        ''' Returns status of user's movies
        :param imdbid: imdb id number of movie <optional>

        Returns list of movie details from MOVIES table. If imdbid is not supplied
            returns all movie details.

        Returns str json.dumps(dict)
        '''

        logging.info('API request movie list.')
        movies = self.sql.get_user_movies()
        if not movies:
            return 'No movies found.'

        if imdbid:
            for i in movies:
                if i['imdbid'] == imdbid:
                    if i['status'] == 'Disabled':
                        i['status'] = 'Finished'
                    response = {'response': True, 'movie': i}
                    return json.dumps(response, indent=1)
        else:
            for i in movies:
                if i['status'] == 'Disabled':
                    i['status'] = 'Finished'
            response = {'response': True, 'movies': movies}
            return json.dumps(response, indent=1)

    def addmovie(self, imdbid=None, tmdbid=None, quality=None):
        ''' Add movie with default quality settings
        :param imdbid: imdb id number of movie

        Returns str json.dumps(dict) {"status": "success", "message": "X added to wanted list."}
        '''

        if quality is None:
            quality = 'Default'

        if imdbid:
            logging.info('API request add movie imdb {}'.format(imdbid))
            return self.ajax.add_wanted_imdbid(imdbid, quality=quality)
        else:
            logging.info('API request add movie tmdb {}'.format(tmdbid))
            return self.ajax.add_wanted_tmdbid(tmdbid, quality=quality)

    def removemovie(self, imdbid):
        ''' Remove movie from wanted list
        :param imdbid: imdb id number of movie

        Returns str json.dumps(dict)
        '''

        logging.info('API request remove movie {}'.format(imdbid))

        t = threading.Thread(target=self.poster.remove_poster, args=(imdbid,))
        t.start()

        removed = self.sql.remove_movie(imdbid)

        if removed is True:
            response = {'response': True, 'removed': imdbid}
        elif removed is False:
            response = {'response': False, 'error': 'unable to remove {}'.format(imdbid)}
        elif removed is None:
            response = {'response': False, 'error': '{} does not exist'.format(imdbid)}

        return json.dumps(response, indent=1)

    def version(self):
        ''' Simple endpoint to return commit hash

        Mostly used to test connectivity without modifying the server.

        Returns str json.dumps(dict)
        '''
        return json.dumps({'response': True, 'version': core.CURRENT_HASH, 'api_version': api_version})

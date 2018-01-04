import core
from core.movieinfo import TMDB
import cherrypy
import threading

import logging


logging = logging.getLogger(__name__)

api_version = 2.2

''' API

All methods output a json object:
{'response': true}

A 'true' response indicates that the request was valid and returns useful data.
A 'false' response indicates that the request was invalid or failed. This will
    always include an 'error' key that describes the reason for the failure.

All successul method calls then append additional key:value pairs to the output json.


# METHODS

mode=liststatus:
    Description:
        Effectively a database dump of the MOVIES table
        Will return one value if imdbid is passed, else returns all movies

    Example:
        Request:
            ?apikey=123456789&mode=liststaus&imdbid=tt1234567
        Response:
            {'movie': {'key': 'value', 'key2', 'value2'}}

        Request:
            ?apikey=123456789&mode=liststaus
        Response:
            {'movies': [{'key': 'value', 'key2', 'value2'}, {'key': 'value', 'key2', 'value2'}]}

mode=addmovie
    Description:
        Adds a movie to the user's library
        Accepts imdb and tmdb id #s
        Imdb id must include 'tt'
        Will add using 'Default' quality profile unless specified otherwise

    Example:
        Request:
            ?apikey=123456789&mode=addmovie&imdbid=tt1234567
        Response:
            {'message': 'MOVIE TITLE YEAR added to wanted list.'}

        Request:
            ?apikey=123456789&mode=addmovie&tmdbid=1234567
        Response:
            {'message': 'MOVIE TITLE YEAR added to wanted list.'}

mode=removemovie
    Description:
        Removes movie from user's library
        Does not remove movie files, only removes entry from Watcher

    Example:
        Request:
            ?apikey=123456789&mode=addmovie&imdbid=tt1234567
        Response:
            {'removed': 'tt1234567'}

mode=getconfig
    Description:
        Returns a dump of the user's config

    Example:
        Request:
            ?apikey=123456789&mode=getconfig
        Response:
            {'config': {'Search': {'etc': 'etc'}}}

mode=version
    Description:
        Returns API version and current git hash of Watcher

    Example:
        Request:
            ?apikey=123456789&mode=version
        Response:
            {'version': '4fcdda1df1a4ff327c3219311578d703a288e598', 'api_version': 1.0}

mode=server_shutdown
    Description:
        Gracefully terminate Watcher server and child processes.
        Shutdown may be instant or delayed to wait for threaded tasks to finish.
        Returns confirmation that request was received.

    Example:
        ?apikey=123456789&mode=shutdown

mode=server_restart
    Description:
        Gracefully restart Watcher server.
        Shutdown may be instant or delayed to wait for threaded tasks to finish.
        Returns confirmation that request was received.

    Example:
        ?apikey=123456789&mode=restart


# API Version
Methods added to the api or minor adjustments to existing methods will increase the version by X.1
Version 1.11 is greater than 1.9
It is safe to assume that these version increases will not break any api interactions

Changes to the output responses will increase the version to the next whole number 2.0
Major version changes can be expected to break api interactions

# VERSION HISTORY
1.0     First commit
1.1     Consistency in responses

2.0     Change to semantically correct json. Responses are now bools instead of str 'true'/'false'
2.1     Adjust addmovie() to pass origin argument. Adjust addmovie() to search tmdb for itself rather than in core.ajax()
2.1     Update documentation for all methods
'''


class API(object):

    def __init__(self):
        self.tmdb = TMDB()
        return

    @cherrypy.expose()
    @cherrypy.tools.json_out()
    def default(self, **params):
        ''' Get handler for API calls

        params: kwargs must inlcude {'apikey': $, 'mode': $}

        Checks api key matches and other required keys are present based on
            mode. Then dispatches to correct method to handle request.
        '''

        logging.info('API request from {}'.format(cherrypy.request.headers['Remote-Addr']))

        serverkey = core.CONFIG['Server']['apikey']

        if 'apikey' not in params:
            logging.warning('API request failed, no key supplied.')
            return {'response': False, 'error': 'no api key supplied'}

        # check for api key
        if serverkey != params['apikey']:
            logging.warning('Invalid API key in request: {}'.format(params['apikey']))
            return {'response': False, 'error': 'incorrect api key'}

        # find what we are going to do
        if 'mode' not in params:
            return {'response': False, 'error': 'no api mode specified'}

        if params['mode'] == 'liststatus':

            if 'imdbid' in params:
                return self.liststatus(imdbid=params['imdbid'])
            else:
                return self.liststatus()

        elif params['mode'] == 'addmovie':
            if 'imdbid' not in params and 'tmdbid' not in params:
                return {'response': False, 'error': 'no movie id supplied'}
            if params.get('imdbid') and params.get('tmdbid'):
                return {'response': False, 'error': 'multiple movie ids supplied'}
            else:
                quality = params.get('quality')
                if params.get('imdbid'):
                    return self.addmovie(imdbid=params['imdbid'], quality=quality)
                elif params.get('tmdbid'):
                    return self.addmovie(tmdbid=params['tmdbid'], quality=quality)
        elif params['mode'] == 'removemovie':
            if 'imdbid' not in params:
                return {'response': False, 'error': 'no imdbid supplied'}
            else:
                imdbid = params['imdbid']
            return self.removemovie(imdbid)

        elif params['mode'] == 'version':
            return self.version()

        elif params['mode'] == 'getconfig':
            return {'response': True, 'config': core.CONFIG}

        elif params['mode'] == 'server_shutdown':
            threading.Timer(1, core.shutdown).start()
            return {'response': True}

        elif params['mode'] == 'server_restart':
            threading.Timer(1, core.restart).start()
            return {'response': True}

        else:
            return {'response': False, 'error': 'invalid mode'}

    def liststatus(self, imdbid=None):
        ''' Returns status of user's movies
        :param imdbid: imdb id number of movie <optional>

        Returns list of movie details from MOVIES table. If imdbid is not supplied
            returns all movie details.

        Returns str dict)
        '''

        logging.info('API request movie list.')
        movies = core.sql.get_user_movies()
        if not movies:
            return 'No movies found.'

        if imdbid:
            for i in movies:
                if i['imdbid'] == imdbid:
                    if i['status'] == 'Disabled':
                        i['status'] = 'Finished'
                    return {'response': True, 'movie': i}
        else:
            for i in movies:
                if i['status'] == 'Disabled':
                    i['status'] = 'Finished'
            return {'response': True, 'movies': movies}

    def addmovie(self, imdbid=None, tmdbid=None, quality=None):
        ''' Add movie with default quality settings
        imdbid (str): imdb id #

        Returns str dict) {'status': 'success', 'message': 'X added to wanted list.'}
        '''

        origin = cherrypy.request.headers.get('User-Agent', 'API')
        origin = 'API' if origin.startswith('Mozilla/') else origin
        if quality is None:
            quality = 'Default'

        if imdbid:
            logging.info('API request add movie imdb {}'.format(imdbid))
            movie = self.tmdb._search_imdbid(imdbid)
            if not movie:
                return {'response': False, 'error': 'Cannot find {} on TMDB'.format(imdbid)}
            else:
                movie = movie[0]
                movie['imdbid'] = imdbid
        elif tmdbid:
            logging.info('API request add movie tmdb {}'.format(tmdbid))
            movie = self.tmdb._search_tmdbid(tmdbid)

            if not movie:
                return {'response': False, 'error': 'Cannot find {} on TMDB'.format(tmdbid)}
            else:
                movie = movie[0]

        movie['quality'] = quality
        movie['status'] = 'Waiting'
        movie['origin'] = origin

        return core.manage.add_movie(movie, full_metadata=True)

    def removemovie(self, imdbid):
        ''' Remove movie from library
        imdbid (str): imdb id #

        Returns str dict)
        '''

        logging.info('API request remove movie {}'.format(imdbid))

        return core.manage.remove_movie(imdbid)

    def version(self):
        ''' Simple endpoint to return commit hash

        Mostly used to test connectivity without modifying the server.

        Returns str dict)
        '''
        return {'response': True, 'version': core.CURRENT_HASH, 'api_version': api_version}

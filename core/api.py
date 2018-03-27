import core
from core.movieinfo import TMDB
import cherrypy
import threading

import logging

logging = logging.getLogger(__name__)

api_version = 2.3

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
        Additional params (besides mode and apikey) will be applied as filters to the movie database
            For example, passing &imdbid=tt1234557 will only return movies with the imdbid tt1234567.
            Multiple filters can be applied using the columns described in core.sql

    Example:
        Request:
            ?apikey=123456789&mode=liststatus
        Response:
            {'movies': [{'key': 'value', 'key2', 'value2'}, {'key': 'value', 'key2', 'value2'}]}

        Request:
            ?apikey=123456789&mode=liststatus&origin=Search
        Response:
            {'movies': [{'key': 'value', 'origin', 'Search'}, {'key': 'value', 'origin', 'Search'}]}

mode=addmovie
    Description:
        Adds a movie to the user's library
        Accepts imdb and tmdb id #s
        Imdb id must include 'tt'
        Will add using Default quality profile unless specified otherwise

    Example:
        Request:
            ?apikey=123456789&mode=addmovie&imdbid=tt1234567&quality=Default
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
2.2     Update documentation for all methods
2.3     Update dispatch method. Allow arbitrary filters in liststatus.
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

        if serverkey != params['apikey']:
            logging.warning('Invalid API key in request: {}'.format(params['apikey']))
            return {'response': False, 'error': 'incorrect api key'}
        params.pop('apikey')

        # find what we are going to do
        if 'mode' not in params:
            return {'response': False, 'error': 'no api mode specified'}

        mode = params.pop('mode')
        if not hasattr(self, mode):
            return {'response': False, 'error': 'unknown method call: {}'.format(mode)}
        else:
            return getattr(self, mode)(params)

    def liststatus(self, filters):
        ''' Returns status of user's movies
        filters (dict): filters to apply to database request

        Returns all movies where col:val pairs match all key:val pairs in filters

        Returns list of movie details from MOVIES table.

        Returns dict
        '''

        logging.info('API request movie list -- filters: {}'.format(filters))
        movies = core.sql.get_user_movies()
        if not movies:
            return {'response': True, 'movies': []}

        for i in filters.keys():
            if i not in core.sql.MOVIES.columns:
                return {'response': False, 'error': 'Invalid filter key: {}'.format(i)}

        return {'response': True, 'movies': [i for i in movies if all(i[k] == v for k, v in filters.items())]}

    # @todo add param checking to each child method
    def addmovie(self, params):
        ''' Add movie with default quality settings
        params (dict): params passed in request url

        Returns dict {'status': 'success', 'message': 'X added to wanted list.'}
        '''

        if not (params.get('imdbid') or params.get('tmdbid')):
            return {'response': False, 'error': 'no movie id supplied'}
        elif (params.get('imdbid') and params.get('tmdbid')):
            return {'response': False, 'error': 'multiple movie ids supplied'}

        origin = cherrypy.request.headers.get('User-Agent', 'API')
        origin = 'API' if origin.startswith('Mozilla/') else origin

        quality = params.get('quality') or core.config.default_profile()

        if params.get('imdbid'):
            imdbid = params['imdbid']
            logging.info('API request add movie imdb {}'.format(imdbid))
            movie = self.tmdb._search_imdbid(imdbid)
            if not movie:
                return {'response': False, 'error': 'Cannot find {} on TMDB'.format(imdbid)}
            else:
                movie = movie[0]
                movie['imdbid'] = imdbid
        elif params.get('tmdbid'):
            tmdbid = params['tmdbid']
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

    def removemovie(self, params):
        ''' Remove movie from library
        params (dict): params passed in request url

        Returns dict
        '''

        if not params.get('imdbid'):
            return {'response': False, 'error': 'no imdbid supplied'}

        logging.info('API request remove movie {}'.format(params['imdbid']))

        return core.manage.remove_movie(params['imdbid'])

    def version(self, *args):
        ''' Simple endpoint to return commit hash
        Mostly used to test connectivity without modifying the server.

        Returns dict
        '''
        return {'response': True, 'version': core.CURRENT_HASH, 'api_version': api_version}

    def getconfig(self, *args):
        ''' Returns config contents as JSON object
        '''
        return {'response': True, 'config': core.CONFIG}

    def server_shutdown(self, *args):
        threading.Timer(1, core.shutdown).start()
        return {'response': True}

    def server_restart(self, *args):
        threading.Timer(1, core.restart).start()
        return {'response': True}

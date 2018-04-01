import logging

import core
from core.providers.base import NewzNabProvider

logging = logging.getLogger(__name__)


class NewzNab(NewzNabProvider):

    def __init__(self):
        self.feed_type = 'nzb'
        return

    # Returns a list of results stored as dicts
    def search_all(self, imdbid):
        ''' Search all Newznab indexers.
        imdbid (str): imdb id #

        Returns list of dicts with sorted nzb information.
        '''

        logging.info('Performing backlog search for all NewzNab indexers.')

        indexers = core.CONFIG['Indexers']['NewzNab'].values()

        results = []

        for indexer in indexers:
            if indexer[2] is False:
                continue
            url_base = indexer[0]
            logging.info('Searching NewzNab indexer {}'.format(url_base))
            if url_base[-1] != '/':
                url_base = url_base + '/'
            apikey = indexer[1]

            r = self.search_newznab(url_base, apikey, 'movie', imdbid=imdbid)
            for i in r:
                results.append(i)

        return results

    def get_rss(self):
        ''' Calls _get_rss from inherited Base class

        Returns list of dicts with parsed nzb info
        '''
        return self._get_rss()

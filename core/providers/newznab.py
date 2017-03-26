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
        :param imdbid: string imdb movie id.

        Returns list of dicts with sorted nzb information.
        '''

        indexers = core.CONFIG['Indexers']['NewzNab'].values()

        self.imdbid = imdbid

        results = []
        imdbid_s = imdbid[2:]  # just imdbid numbers

        for indexer in indexers:
            if indexer[2] is False:
                continue
            url_base = indexer[0]
            if url_base[-1] != '/':
                url_base = url_base + '/'
            apikey = indexer[1]

            r = self.search_newznab(url_base, apikey, t='movie', imdbid=imdbid_s)
            for i in r:
                results.append(i)

        self.imdbid = None
        return results

    def get_rss(self):
        return self._get_rss()

import datetime
import logging

import core
from core import scoreresults, snatcher, sqldb, updatestatus, proxy
from core.providers import torrent, newznab
from core.rss import predb
from fuzzywuzzy import fuzz

logging = logging.getLogger(__name__)


class Searcher():

    def __init__(self):
        self.nn = newznab.NewzNab()
        self.score = scoreresults.ScoreResults()
        self.sql = sqldb.SQL()
        self.predb = predb.PreDB()
        self.snatcher = snatcher.Snatcher()
        self.torrent = torrent.Torrent()
        self.update = updatestatus.Status()

    def auto_search_and_grab(self):
        ''' Scheduled searcher and grabber.

        Runs search when scheduled. ONLY runs when scheduled.
        Runs in its own thread.

        First checks for all movies on predb.

        Searches only for movies where predb == 'found'.

        Searches only for movies that are Wanted, Found,
            or Finished -- if inside user-set date range.

        Checks each movie's backlog status. Runs a backlog search if neccesary, else Looks
            in RSS feeds for any matches.

        Will grab movie if autograb is 'true' and
            movie is 'Found' or 'Finished'.

        Updates core.NEXT_SEARCH time

        Does not return
        '''

        interval = core.CONFIG['Search']['rsssyncfrequency'] * 60
        now = datetime.datetime.today().replace(second=0, microsecond=0)
        core.NEXT_SEARCH = now + datetime.timedelta(0, interval)

        today = datetime.date.today()
        keepsearching = core.CONFIG['Search']['keepsearching']
        keepsearchingdays = core.CONFIG['Search']['keepsearchingdays']
        keepsearchingdelta = datetime.timedelta(days=keepsearchingdays)
        auto_grab = core.CONFIG['Search']['autograb']

        self.predb.check_all()
        logging.info('############# Running automatic search #############')
        if keepsearching is True:
            logging.info('Search for Finished movies enabled. Will search again for any movie that has finished in the last {} days.'.format(keepsearchingdays))
        movies = self.sql.get_user_movies()
        if not movies:
            return False

        # Get movies that require backlog search and execute it
        backlog_movies = self._get_backlog_movies(movies)

        if backlog_movies:
            logging.info('Performing backlog search for {} movies.'.format(len(backlog_movies)))
            logging.debug('Backlog movies: {}'.format(backlog_movies))
            for movie in backlog_movies:
                if movie['predb'] != 'found':
                    continue
                imdbid = movie['imdbid']
                title = movie['title']
                year = movie['year']
                quality = movie['quality']
                status = movie['status']

                logging.info('Executing backlog search for {} {}.'.format(title, year))
                self.search(imdbid, title, year, quality)
                continue

        rss_movies = self._get_rss_movies(movies)

        if rss_movies:
            logging.info('Checking RSS feeds for {} movies.'.format(len(rss_movies)))
            self.rss_sync(rss_movies)

        '''
        If autograb is enabled, loops through movies and grabs any appropriate releases.
        '''
        if auto_grab is True:
            logging.info('############ Running automatic snatcher ############')
            keepsearchingscore = core.CONFIG['Search']['keepsearchingscore']
            # In case we found something we'll check this again.
            movies = self.sql.get_user_movies()
            if not movies:
                return False
            for movie in movies:
                status = movie['status']
                if status == 'Disabled':
                    continue
                imdbid = movie['imdbid']
                title = movie['title']
                year = movie['year']
                quality = movie['quality']

                if status == 'Found':
                    logging.info('{} status is Found. Running automatic snatcher.'.format(title))
                    self.snatcher.auto_grab(movie)
                    continue

                if status == 'Finished' and keepsearching is True:
                    finished_date = movie['finished_date']
                    finished_date_obj = datetime.datetime.strptime(finished_date, '%Y-%m-%d').date()
                    if finished_date_obj + keepsearchingdelta >= today:
                        minscore = movie['finished_score'] + keepsearchingscore
                        logging.info('{} {} was marked Finished on {}. Checking for a better release (min score {}).'.format(title, year, finished_date, minscore))
                        self.snatcher.auto_grab(movie, minscore=minscore)
                        continue
                    else:
                        continue
                else:
                    continue
        logging.info('######### Automatic search/snatch complete #########')
        return

    def search(self, imdbid, title, year, quality):
        ''' Executes backlog search for required movies
        imdbid: str imdb identification number
        title: str movie title
        year: str year of movie release
        quality: str name of quality profile.

        Gets new search results from newznab providers.
        Pulls existing search results and updates new data with old. This way the
            found_date doesn't change and scores can be updated if the quality profile
            was modified since last search.

        Sends ALL results to scoreresults.score() to be (re-)scored and filtered.

        Checks if guid matches entries in MARKEDRESULTS and
            sets status if found. Default status Available.

        Finally stores results in SEARCHRESULTS

        Returns Bool if movie is found.
        '''

        proxy.Proxy.create()

        results = []

        if core.CONFIG['Downloader']['Sources']['usenetenabled']:
            for i in self.nn.search_all(imdbid):
                results.append(i)
        if core.CONFIG['Downloader']['Sources']['torrentenabled']:
            for i in self.torrent.search_all(imdbid, title, year):
                results.append(i)

        proxy.Proxy.destroy()

        old_results = [dict(r) for r in self.sql.get_search_results(imdbid, quality)]

        for old in old_results:
            if old['type'] == 'import':
                results.append(old)

        active_old_results = self.remove_inactive(old_results)

        # update results with old info if guids match
        for idx, result in enumerate(results):
            for old in active_old_results:
                if old['guid'] == result['guid']:
                    result.update(old)
                    results[idx] = result

        for idx, result in enumerate(results):
            results[idx]['resolution'] = self.get_source(result)

        scored_results = self.score.score(results, imdbid=imdbid)

        # sets result status based off marked results table
        marked_results = self.sql.get_marked_results(imdbid)
        if marked_results:
            for result in scored_results:
                if result['guid'] in marked_results:
                    result['status'] = marked_results[result['guid']]

        if not self.store_results(scored_results, imdbid, backlog=True):
            logging.error('Unable to store search results for {}'.format(imdbid))
            return False

        if not self.update.movie_status(imdbid):
            logging.error('Unable to update movie status for {}'.format(imdbid))
            return False

        if not self.sql.update('MOVIES', 'backlog', '1', 'imdbid', imdbid):
            logging.error('Unable to flag backlog search as complete for {}'.format(imdbid))
            return False

        return True

    def rss_sync(self, movies):
        ''' Gets latests RSS feed from all indexers
        movies: list of dicts of movies to look for

        Gets latest rss feed from all supported indexers.

        Looks through rss for anything that matches a movie in 'movies'

        Only stores new results. If you need to update scores or old results
            force a backlog search.

        Finally stores results in SEARCHRESULTS

        Does not return
        '''
        newznab_results = []
        torrent_results = []

        proxy.Proxy.create()

        if core.CONFIG['Downloader']['Sources']['usenetenabled']:
            newznab_results = self.nn.get_rss()
        if core.CONFIG['Downloader']['Sources']['torrentenabled']:
            torrent_results = self.torrent.get_rss()

        proxy.Proxy.destroy()

        for movie in movies:
            imdbid = movie['imdbid']
            title = movie['title']
            year = movie['year']

            nn_found = [i for i in newznab_results if i['imdbid'] == imdbid]

            tor_found = [i for i in torrent_results if
                         self._match_torrent_name(title, year, i['title'])]
            for idx, result in enumerate(tor_found):
                result['imdbid'] = imdbid
                tor_found[idx] = result

            results = nn_found + tor_found

            if not results:
                continue

            # Ignore results we've already stored
            old_results = [dict(r) for r in self.sql.get_search_results(imdbid)]
            new_results = []
            for res in results:
                guid = res['guid']
                if all(guid != i['guid'] for i in old_results):
                    new_results.append(res)
                else:
                    continue

            logging.info('Found {} new results for {} {}.'.format(len(new_results), title, year))

            # Get source media and resolution
            for idx, result in enumerate(new_results):
                new_results[idx]['resolution'] = self.get_source(result)

            scored_results = self.score.score(new_results, imdbid=imdbid)

            if len(scored_results) == 0:
                continue

            if not self.store_results(scored_results, imdbid):
                return False

            if not self.update.movie_status(imdbid):
                logging.info('No acceptable results found for {}'.format(imdbid))
                return False

        return True

    def remove_inactive(self, results):
        ''' Removes results from indexers no longer enabled
        results: list of dicts of search results

        Pulls active indexers from config, then removes any
            result that isn't from an active indexer.

        Does not filter Torrent results.
            Since torrent names don't always match their domain
            ie demonoid == dnoid.me, we can't filter out disabled torrent
            indexers since all would be removed

        returns list of search results to keep
        '''

        active = []
        for i in core.CONFIG['Indexers']['NewzNab'].values():
            if i[2] is True:
                active.append(i[0])

        keep = []
        for result in results:
            if result['type'] in ['torrent', 'magnet', 'import']:
                keep.append(result)
            for indexer in active:
                if indexer in result['guid']:
                    keep.append(result)

        return keep

    def store_results(self, results, imdbid, backlog=False):
        ''' Stores search results in database.
        :param results: list of dicts of search results
        :param imdbid: str imdb identification number (tt123456)
        backlog: Bool if this call is from a backlog search <default False>

        Writes batch of search results to table.

        If storing backlog search results, will purge existing results. This is because
            backlog searches pull all existing results from the table and re-score them
            as to not change the found_date. Purging lets us write old results back in
            with updated scores and other info.

        Returns Bool on success/failure.
        '''

        logging.info('{} results found for {}. Storing results.'.format(len(results), imdbid))

        BATCH_DB_STRING = []

        for result in results:
            DB_STRING = result
            DB_STRING['imdbid'] = imdbid
            if 'date_found' not in DB_STRING:
                DB_STRING['date_found'] = datetime.date.today()
            BATCH_DB_STRING.append(DB_STRING)

        if backlog:
            self.sql.purge_search_results(imdbid=imdbid)

        if BATCH_DB_STRING:
            if self.sql.write_search_results(BATCH_DB_STRING):
                return True
            else:
                return False
        else:
            return True

    def get_source(self, result):
        ''' Parses release resolution and source from title.
        :param result: dict of individual search result info

        Returns str source based on core.RESOLUTIONS
        '''

        title = result['title']
        if '4K' in title or 'UHD' in title or '2160P' in title:
            resolution = '4K'
        elif '1080' in title:
            resolution = '1080P'
        elif '720' in title:
            resolution = '720P'
        else:
            resolution = 'SD'

        delimiters = ['.', '_', ' ', '-', '+']
        brk = False
        for source, aliases in core.CONFIG['Quality']['Aliases'].items():
            for a in aliases:
                aliases_delimited = ['{}{}'.format(d, a) for d in delimiters]
                if any(i in title.lower() for i in aliases_delimited):
                    return '{}-{}'.format(source, resolution)
                    brk = True
                    break
            if brk is True:
                break
        return 'Unknown-{}'.format(resolution)

    def _get_backlog_movies(self, movies):
        ''' Gets list of movies that require backlog search
        movies: list of dicts of movie rows in movies

        Filters movies so it includes movies where backlog == 0 and
            status is Wanted, Found, or Finished

        Returns list of dicts of movies that require backlog search
        '''

        backlog_movies = []

        for i in movies:
            if i['predb'] != 'found':
                continue
            if i['backlog'] != 1 and i['status'] in ('Wanted', 'Found', 'Finished'):
                logging.info('{} {} has not yet recieved a full backlog search, will execute.'.format(i['title'], i['year']))
                backlog_movies.append(i)

        return backlog_movies

    def _get_rss_movies(self, movies):
        ''' Gets list of movies that we'll look in the rss feed for
        movies: list of dicts of movie rows in movies

        Filters movies so it includes movies where backlog == 1 and
            status is Wanted, Found, Snatched, or Finished
        If status is Finished checks if it is within the KeepSearching window

        Returns list of dicts of movies that require backlog search
        '''
        today = datetime.date.today()
        keepsearching = core.CONFIG['Search']['keepsearching']
        keepsearchingdays = core.CONFIG['Search']['keepsearchingdays']
        keepsearchingdelta = datetime.timedelta(days=keepsearchingdays)

        rss_movies = []

        for i in movies:
            if i['backlog'] != 1:
                continue
            if i['predb'] != 'found':
                continue

            title = i['title']
            year = i['year']
            status = i['status']

            if status in ['Wanted', 'Found', 'Snatched']:
                rss_movies.append(i)
                logging.info('{} {} is {}. Will look for new releases in RSS feed.'.format(title, year, status))
            if status == 'Finished' and keepsearching is True:
                finished_date_obj = datetime.datetime.strptime(i['finished_date'], '%Y-%m-%d').date()
                if finished_date_obj + keepsearchingdelta >= today:
                    logging.info('{} {} was marked Finished on {}, will keep checking RSS feed for new releases.'.format(title, year, i['finished_date']))
                    rss_movies.append(i)
                continue

        return rss_movies

    def _match_torrent_name(self, movie_title, movie_year, torrent_title):
        ''' Checks if movie_title and torrent_title are a good match
        movie_title: str title of movie
        movie_year: str year of movie release
        torrent_title: str title of torrent

        Helper function for rss_sync.

        Since torrent indexers don't supply imdbid like NewzNab does we have to compare
            the titles to find a match. This should be fairly accurate since a backlog
            search uses name and year to find releases.

        Checks if the year is in the title, promptly ignores it if the year is not found.
        Then does a fuzzy title match looking for 80+ token set ratio.

        Returns bool on match success
        '''

        if movie_year not in torrent_title:
            return False
        else:
            title = movie_title.replace(':', '.').replace(' ', '.').lower()
            torrent = torrent_title.replace(' ', '.').replace(':', '.').lower()
            match = fuzz.token_set_ratio(title, torrent)
            if match > 80:
                return True
            else:
                return False

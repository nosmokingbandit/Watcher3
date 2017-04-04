import logging

from core import sqldb, library, scoreresults, searcher
import os

logging = logging.getLogger(__name__)


class Status(object):

    def __init__(self):
        self.sql = sqldb.SQL()
        self.library = library.ImportDirectory()
        self.score = scoreresults.ScoreResults()

    def searchresults(self, guid, status, movie_info=None):
        ''' Marks searchresults status
        :param guid: str download link guid
        :param status: str status to set
        movie_info: dict of movie metadata

        If guid is in SEARCHRESULTS table, marks it as status.

        If guid not in SEARCHRESULTS, uses movie_info to create a result.

        Returns Bool on success/fail
        '''

        TABLE = 'SEARCHRESULTS'

        logging.info('Marking guid {} as {}.'.format(guid.split('&')[0], status))

        if self.sql.row_exists(TABLE, guid=guid):

            # Mark bad in SEARCHRESULTS
            logging.info('Marking {} as {} in SEARCHRESULTS.'.format(guid.split('&')[0], status))
            if not self.sql.update(TABLE, 'status', status, 'guid', guid):
                logging.error('Setting SEARCHRESULTS status of {} to {} failed.'.format(guid.split('&')[0], status))
                return False
            else:
                logging.info('Successfully marked {} as {} in SEARCHRESULTS.'.format(guid.split('&')[0], status))
                return True
        else:
            logging.info('Guid {} not found in SEARCHRESULTS, attempting to create entry.'.format(guid.split('&')[0]))
            if movie_info is None:
                logging.warning('Metadata not supplied, unable to create SEARCHRESULTS entry.')
                return False
            search_result = searcher.Searcher.fake_search_result(movie_info)
            search_result['indexer'] = 'Post-Processing Import'
            search_result['title'] = movie_info['title']
            search_result['size'] = os.path.getsize(movie_info.get('orig_filename', '.'))
            if not search_result['resolution']:
                search_result['resolution'] = 'Unknown'

            search_result = self.score.score([search_result], imported=True)[0]

            if self.sql.write('SEARCHRESULTS', search_result):
                return True
            else:
                return False

    def markedresults(self, guid, status, imdbid=None):
        ''' Marks markedresults status
        :param guid: str download link guid
        :param status: str status to set
        :param imdbid: str imdb identification number   <optional>

        imdbid can be None

        If guid is in MARKEDRESULTS table, marks it as status.
        If guid not in MARKEDRSULTS table, created entry. Requires imdbid.

        Returns Bool on success/fail
        '''

        TABLE = 'MARKEDRESULTS'

        if self.sql.row_exists(TABLE, guid=guid):
            # Mark bad in MARKEDRESULTS
            logging.info('Marking {} as {} in MARKEDRESULTS.'.format(guid.split('&')[0], status))
            if not self.sql.update(TABLE, 'status', status, 'guid', guid):
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
                if self.sql.write(TABLE, DB_STRING):
                    logging.info('Successfully created entry in MARKEDRESULTS for {}.'.format(guid.split('&')[0]))
                    return True
                else:
                    logging.error('Unable to create entry in MARKEDRESULTS for {}.'.format(guid.split('&')[0]))
                    return False
            else:
                logging.warning('Imdbid not supplied or found, unable to add entry to MARKEDRESULTS.')
                return False

    def mark_bad(self, guid, imdbid=None):
        ''' Marks search result as Bad
        :param guid: str download link for nzb/magnet/torrent file.

        Calls self method to update both db tables
        Tries to find imdbid if not supplied.
        If imdbid is available or found, executes self.movie_status()

        Returns bool
        '''

        if not self.searchresults(guid, 'Bad'):
            return 'Could not mark guid in SEARCHRESULTS. See logs for more information.'

        # try to get imdbid
        if imdbid is None:
            result = self.sql.get_single_search_result('guid', guid)
            if not result:
                return False
            else:
                imdbid = result['imdbid']

        if not self.movie_status(imdbid):
            return False

        if not self.markedresults(guid, 'Bad', imdbid=imdbid):
            return False
        else:
            return True

    def movie_status(self, imdbid):
        ''' Updates Movie status.
        :param imdbid: str imdb identification number (tt123456)

        Updates Movie status based on search results.
        Always sets the status to the highest possible level.

        Returns bool on success/failure.
        '''

        local_details = self.sql.get_movie_details('imdbid', imdbid)
        if local_details:
            current_status = local_details.get('status')
        else:
            return True

        if current_status == 'Disabled':
            return True

        result_status = self.sql.get_distinct('SEARCHRESULTS', 'status', 'imdbid', imdbid)
        if result_status is False:
            logging.error('Could not get SEARCHRESULTS statuses for {}'.format(imdbid))
            return False
        elif result_status is None:
            status = 'Wanted'
        else:
            if 'Finished' in result_status:
                status = 'Finished'
            elif 'Snatched' in result_status:
                status = 'Snatched'
            elif 'Available' in result_status:
                status = 'Found'
            else:
                status = 'Wanted'

        logging.info('Setting MOVIES {} status to {}.'.format(imdbid, status))
        if self.sql.update('MOVIES', 'status', status, 'imdbid', imdbid):
            return True
        else:
            logging.error('Could not set {} to {}'.format(imdbid, status))
            return False

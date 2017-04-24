import core
import datetime
import logging
import time
import os
import shutil

from core.helpers import Comparisons
from sqlalchemy import *

logging = logging.getLogger(__name__)


class SQL(object):
    '''
    All methods will return False on failure.
    On success they will return the expected data or True.
    '''

    def __init__(self):
        DB_NAME = 'sqlite:///{}'.format(core.DB_FILE)
        try:
            self.engine = create_engine(DB_NAME, echo=False, connect_args={'timeout': 30})
            self.metadata = MetaData()
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e: # noqa
            logging.error('Opening SQL DB.', exc_info=True)
            raise

        # These definitions only exist to CREATE tables.
        self.MOVIES = Table('MOVIES', self.metadata,
                            Column('added_date', TEXT),
                            Column('imdbid', TEXT),
                            Column('title', TEXT),
                            Column('year', TEXT),
                            Column('poster', TEXT),
                            Column('plot', TEXT),
                            Column('url', TEXT),
                            Column('score', TEXT),
                            Column('release_date', TEXT),
                            Column('rated', TEXT),
                            Column('status', TEXT),
                            Column('predb', TEXT),
                            Column('quality', TEXT),
                            Column('finished_date', TEXT),
                            Column('finished_score', SMALLINT),
                            Column('finished_file', TEXT),
                            Column('backlog', SMALLINT),
                            Column('tmdbid', TEXT),
                            Column('alternative_titles', TEXT),
                            Column('digital_release_date', TEXT)
                            )
        self.SEARCHRESULTS = Table('SEARCHRESULTS', self.metadata,
                                   Column('score', SMALLINT),
                                   Column('size', SMALLINT),
                                   Column('status', TEXT),
                                   Column('pubdate', TEXT),
                                   Column('title', TEXT),
                                   Column('imdbid', TEXT),
                                   Column('indexer', TEXT),
                                   Column('date_found', TEXT),
                                   Column('info_link', TEXT),
                                   Column('guid', TEXT),
                                   Column('torrentfile', TEXT),
                                   Column('resolution', TEXT),
                                   Column('type', TEXT),
                                   Column('downloadid', TEXT),
                                   Column('freeleech', SMALLINT)
                                   )
        self.MARKEDRESULTS = Table('MARKEDRESULTS', self.metadata,
                                   Column('imdbid', TEXT),
                                   Column('guid', TEXT),
                                   Column('status', TEXT)
                                   )
        self.CAPS = Table('CAPS', self.metadata,
                          Column('url', TEXT),
                          Column('caps', TEXT)
                          )

        # {TABLENAME: [(new_col, old_col), (new_col, old_col)]}
        self.convert_names = {'MOVIES':
                              [('url', 'tomatourl'),
                               ('score', 'tomatorating'),
                               ('release_date', 'released'),
                               ('finished_date', 'finisheddate')
                               ]}

    def create_database(self):
        logging.info('Creating tables.')
        self.metadata.create_all(self.engine)
        return

    def execute(self, command):
        ''' Executes SQL command
        command: str or list of SQL commands

        We are going to loop this up to 5 times in case the database is locked.
        After each attempt we wait 1 second to try again. This allows the query
            that has the database locked to (hopefully) finish. It might
            (i'm not sure) allow a query to jump in line between a series of
            queries. So if we are writing searchresults to every movie at once,
            the get_user_movies request may be able to jump in between them to
            get the user's movies to the browser. Maybe.

        Returns result of command, or False if unable to execute
        '''

        tries = 0
        while tries < 5:
            try:
                if type(command) == list:
                    result = self.engine.execute(*command)
                else:
                    result = self.engine.execute(command)
                return result

            except Exception as e:
                logging.error('SQL Database Query: {}.'.format(command), exc_info=True)
                if 'database is locked' in e.args[0]:
                    logging.debug('SQL Query attempt # {}.'.format(tries))
                    tries += 1
                    time.sleep(1)
                else:
                    logging.error('SQL Databse Query: {}.'.format(command), exc_info=True)
                    raise
        # all tries exhausted
        return False

    def write(self, TABLE, DB_STRING):
        ''' Writes row to table
        TABLE: str name of db table
        DB_STRING: dict of columns:values to write

        Returns Bool on success.
        '''

        logging.info('Writing data to {}.'.format(TABLE))

        cols = ', '.join(DB_STRING.keys())
        vals = list(DB_STRING.values())

        qmarks = ', '.join(['?'] * len(DB_STRING))

        sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (TABLE, cols, qmarks)

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to write to database.')
            return False

    def write_search_results(self, LIST):
        '''
        Takes list of dicts to write into SEARCHRESULTS.
        '''

        if not LIST:
            return True

        logging.info('Writing batch into SEARCHRESULTS.')

        INSERT = self.SEARCHRESULTS.insert()

        command = [INSERT, LIST]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to write search results.')
            return False

    def update(self, TABLE, COLUMN, VALUE, idcol, idval):
        '''
        Updates single value in existing table row.
        Selects row to update from imdbid or guid.
        Sets COLUMN to VALUE.
        Returns Bool.
        '''

        logging.info('Updating {} to {} for col {}:{} in {}.'.format(COLUMN, VALUE, idcol, idval.split('&')[0], TABLE))

        sql = 'UPDATE {} SET {}=? WHERE {}=?'.format(TABLE, COLUMN, idcol)
        vals = (VALUE, idval)

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to update database row.')
            return False

    def update_multiple(self, TABLE, data, imdbid='', guid=''):
        ''' Updates mulitple values in sql row
        TABLE: str database table to access
        data: dict key/value pairs to update in table
        imdbid: str imdbid # of movie to update
        guid: str guid of search result to update

        Return bool.
        '''

        if imdbid:
            idcol = 'imdbid'
            idval = imdbid
        elif guid:
            idcol = 'guid'
            idval = guid
        else:
            return 'ID ERROR'

        logging.info('Updating {} in {}.'.format(idval.split('&')[0], TABLE))

        columns = '{}=?'.format('=?,'.join(data.keys()))

        sql = 'UPDATE {} SET {} WHERE {}=?'.format(TABLE, columns, idcol)

        vals = tuple(list(data.values()) + [idval])

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to update database row.')
            return False

    def get_user_movies(self):
        ''' Gets all info in MOVIES

        Returns list of dicts with all information in MOVIES
        '''

        logging.info('Retrieving list of user\'s movies.')
        TABLE = 'MOVIES'

        command = 'SELECT * FROM {} ORDER BY title ASC'.format(TABLE)

        result = self.execute(command)

        if result:
            lst = []
            for i in result:
                lst.append(dict(i))
            return lst
        else:
            logging.error('Unable to get list of user\'s movies.')
            return False

    def get_movie_details(self, idcol, idval):
        ''' Returns dict of single movie details from MOVIES.
        :param idcol: str identifying column
        :param idval: str identifying value

        Looks through MOVIES for idcol:idval

        Returns dict of first match
        '''

        logging.info('Retrieving details for {}.'.format(idval))

        command = 'SELECT * FROM MOVIES WHERE {}="{}"'.format(idcol, idval)

        result = self.execute(command)

        if result:
            data = result.fetchone()
            if data:
                return dict(data)
            else:
                return False
        else:
            return False

    def get_search_results(self, imdbid, quality=None):
        ''' Gets all search results for a given movie
        :param imdbid: str imdb id #
        quality: str name of quality profile. Used to sort order <optional>

        Gets all search results sorted by score, then size.

        Looks at quality to determine size sort direction. If not passed defaults to
            DESC, with bigger files first.

        Returns list of dicts for all SEARCHRESULTS that match imdbid
        '''

        if quality in core.CONFIG['Quality']['Profiles'] and core.CONFIG['Quality']['Profiles'][quality]['prefersmaller']:
            sort = 'ASC'
        else:
            sort = 'DESC'

        logging.info('Retrieving Search Results for {}.'.format(imdbid))
        TABLE = 'SEARCHRESULTS'

        command = 'SELECT * FROM {} WHERE imdbid="{}" ORDER BY score DESC, size {}, freeleech DESC'.format(TABLE, imdbid, sort)

        results = self.execute(command)

        if results:
            res = results.fetchall()
            return [dict(i) for i in res]
        else:
            return False

    def get_marked_results(self, imdbid):
        ''' Gets all entries in MARKEDRESULTS for given movie
        :param imdbid: str imdb id #

        Returns dict {guid:status, guid:status, etc}
        '''

        logging.info('Retrieving Marked Results for {}.'.format(imdbid))

        TABLE = 'MARKEDRESULTS'

        results = {}

        command = 'SELECT * FROM {} WHERE imdbid="{}"'.format(TABLE, imdbid)

        data = self.execute(command)

        if data:
            for i in data.fetchall():
                results[i['guid']] = i['status']
            return results
        else:
            return False

    def remove_movie(self, imdbid):
        ''' Removes movie and search results from DB
        :param imdbid: str imdb id #

        Doesn't access sql directly, but instructs other methods to delete all information that matches imdbid.

        Removes from MOVIE, SEARCHRESULTS, and deletes poster. Keeps MARKEDRESULTS.

        Returns True/False on success/fail or None if movie doesn't exist in DB.
        '''

        logging.info('Removing {} from {}.'.format(imdbid, 'MOVIES'))

        if not self.row_exists('MOVIES', imdbid=imdbid):
            return None

        if not self.delete('MOVIES', 'imdbid', imdbid):
            return False

        logging.info('Removing any stored search results for {}.'.format(imdbid))

        if self.row_exists('SEARCHRESULTS', imdbid):
            if not self.purge_search_results(imdbid=imdbid):
                return False

        logging.info('{} removed.'.format(imdbid))
        return True

    def delete(self, TABLE, idcol, idval):
        ''' Deletes row where idcol == idval
        :param idcol: str identifying column
        :param idval: str identifying value

        Returns Bool.
        '''

        logging.info('Removing from {} where {} is {}.'.format(TABLE, idcol, idval.split('&')[0]))

        command = 'DELETE FROM {} WHERE {}="{}"'.format(TABLE, idcol, idval)

        if self.execute(command):
            return True
        else:
            return False

    def purge_search_results(self, imdbid=''):
        ''' Deletes all search results
        :param imdbid: str imdb id # <optional>

        Be careful with this one. Supplying an imdbid deletes search results for that
            movie. If you do not supply an imdbid it purges FOR ALL MOVIES.

        BE CAREFUL.

        Returns Bool
        '''

        TABLE = 'SEARCHRESULTS'

        if imdbid:
            command = 'DELETE FROM {} WHERE imdbid="{}"'.format(TABLE, imdbid)
        else:
            command = 'DELETE FROM {}'.format(TABLE)

        if self.execute(command):
            return True
        else:
            return False

    def get_distinct(self, TABLE, column, idcol, idval):
        ''' Gets unique values in TABLE
        :param TABLE: str table name
        :param column: str column to return
        :param idcol: str identifying column
        :param idval: str identifying value

        Gets values in TABLE:column where idcol == idval

        Returns list ['val1', 'val2', 'val3']
        '''

        logging.info('Getting distinct values for {} in {}'.format(idval.split('&')[0], TABLE))

        command = 'SELECT DISTINCT {} FROM {} WHERE {}="{}"'.format(column, TABLE, idcol, idval)

        data = self.execute(command)

        if data:
            data = data.fetchall()

            if len(data) == 0:
                return None

            lst = []
            for i in data:
                lst.append(i[column])
            return lst
        else:
            logging.error('Unable to read database.')
            return False

    def row_exists(self, TABLE, imdbid='', guid='', downloadid=''):
        ''' Checks if row exists in table
        :param TABLE: str name of sql table to look through
        :param imdbid: str imdb identification number <optional>
        :param guid: str download guid <optional>
        :param downloadid: str downloader id <optional>

        Checks TABLE for imdbid, guid, or downloadid.
        Exactly one optional variable must be supplied.

        Used to check if we need to add row or update existing row.

        Returns Bool of found status
        '''

        if imdbid:
            idcol = 'imdbid'
            idval = imdbid
        elif guid:
            idcol = 'guid'
            idval = guid
        elif downloadid:
            idcol = 'downloadid'
            idval = downloadid

        else:
            return 'ID ERROR'

        command = 'SELECT 1 FROM {} WHERE {}="{}"'.format(TABLE, idcol, idval)

        row = self.execute(command)

        if row is False or row.fetchone() is None:
            return False
        else:
            return True

    def get_single_search_result(self, idcol, idval):
        ''' Gets single search result
        :param idcol: str identifying column
        :param idval: str identifying value

        Finds in SEARCHRESULTS a row where idcol == idval

        Returns dict
        '''

        logging.info('Retrieving search result details for {}.'.format(idval.split('&')[0]))

        command = 'SELECT * FROM SEARCHRESULTS WHERE {}="{}"'.format(idcol, idval)

        result = self.execute(command)

        if result:
            return result.fetchone()
        else:
            return False

    def _get_existing_schema(self):
        table_dict = {}

        # get list of tables in db:
        command = 'SELECT name FROM sqlite_master WHERE type="table"'
        tables = self.execute(command)

        table_dict = {}

        if not tables:
            return False

        for i in tables:
            i = i[0]
            command = 'PRAGMA table_info({})'.format(i)
            columns = self.execute(command)
            if not columns:
                continue
            tmp_dict = {}
            for col in columns:
                tmp_dict[col['name']] = col['type']
            table_dict[i] = tmp_dict

        return table_dict

    def _get_intended_schema(self):
        d = {}
        for table in self.metadata.tables.keys():
            selftable = getattr(self, table)
            d2 = {}
            for i in selftable.c:
                d2[i.name] = str(i.type)
            d[table] = d2
        return d

    def update_tables(self):

        for i in self.get_user_movies():
            if i['predb'] is None and i['status'] is 'Wanted':
                self.update('MOVIES', 'status', 'Waiting', 'imdbid', i['imdbid'])

        existing = self._get_existing_schema()
        intended = self._get_intended_schema()

        diff = Comparisons.compare_dict(intended, existing)

        if not diff:
            return True

        print('Database update required. This may take some time.')

        backup_dir = os.path.join(core.PROG_PATH, 'db')
        logging.info('Backing up database to {}.'.format(backup_dir))
        print('Backing up database to {}.'.format(backup_dir))
        try:
            if not os.path.isdir(backup_dir):
                os.mkdir(backup_dir)
            backup = '{}.{}'.format(core.DB_FILE, datetime.date.today())
            shutil.copyfile(core.DB_FILE, os.path.join(backup_dir, backup))
        except Exception as e: # noqa
            print('Error backing up database.')
            logging.error('Copying SQL DB.', exc_info=True)
            raise

        logging.info('Modifying database tables.')
        print('Modifying tables.')

        '''
        For each item in diff, create new column.
        Then, if the new columns name is in self.convert_names, copy data from old column
        Create the new table, then copy data from TMP table
        '''
        for table, schema in diff.items():
            if table not in existing:
                logging.info('Creating table {}'.format(table))
                print('Creating table {}'.format(table))
                getattr(self, table).create(self.engine)
                continue
            logging.info('Modifying table {}.'.format(table))
            print('Modifying table {}'.format(table))
            for name, kind in schema.items():
                command = 'ALTER TABLE {} ADD COLUMN {} {}'.format(table, name, kind)

                self.execute(command)

                if table in self.convert_names.keys():
                    for pair in self.convert_names[table]:
                        if pair[0] == name:
                            command = 'UPDATE {} SET {} = {}'.format(table, pair[0], pair[1])
                            self.execute(command)

            # move TABLE to TABLE_TMP
            table_tmp = '{}_TMP'.format(table)
            logging.info('Renaming table to {}.'.format(table_tmp))
            print('Renaming table to {}'.format(table_tmp))
            command = 'ALTER TABLE {} RENAME TO {}'.format(table, table_tmp)
            self.execute(command)

            # create new table
            logging.info('Creating new table {}.'.format(table))
            print('Creating new table {}'.format(table))
            table_meta = getattr(self, table)
            table_meta.create(self.engine)

            # copy data over
            logging.info('Merging data from {} to {}.'.format(table_tmp, table))
            print('Merging data from {} to {}'.format(table_tmp, table))
            names = ', '.join(intended[table].keys())
            command = 'INSERT INTO {} ({}) SELECT {} FROM {}'.format(table, names, names, table_tmp)
            self.execute(command)

            logging.info('Dropping table {}.'.format(table_tmp))
            print('Dropping table {}'.format(table_tmp))
            command = 'DROP TABLE {}'.format(table_tmp)
            self.execute(command)

            logging.info('Finished updating table {}.'.format(table))
            print('Finished updating table {}'.format(table))

        logging.info('Database updated')
        print('Database updated.')

    def torznab_caps(self, url):
        ''' Gets caps list for torznab providers
        url: str url of torznab indexer

        Returns list of caps ie ['q', 'imdbid'] or None if not found
        '''

        logging.info('Retreiving caps for {}'.format(url))

        command = 'SELECT "caps" FROM CAPS WHERE url="{}"'.format(url)

        row = self.execute(command)
        caps = row.fetchone()
        if caps is None:
            return None
        else:
            return caps[0].split(',')

# pylama:ignore=W0401

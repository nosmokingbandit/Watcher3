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
    Class to handle all database interactions

    SQL.convert_names is used to convert column names in a table.
        This should be formatted as {TABLE: [(new_column, old_column)],
                                     TABLE2: [(new_column, old_column), (new_column_2, old_column_2)]
                                     }

    '''

    convert_names = {"MOVIES":
                     [("url", "tomatourl"),
                      ("score", "tomatorating"),
                      ("release_date", "released"),
                      ("finished_date", "finisheddate"),
                      ("media_release_date", "digital_release_date")]
                     }

    def __init__(self):
        self.metadata = MetaData()
        DB_NAME = 'sqlite:///{}'.format(core.DB_FILE)

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
                            Column('predb_backlog', TEXT),
                            Column('predb', TEXT),
                            Column('quality', TEXT),
                            Column('finished_date', TEXT),
                            Column('finished_score', SMALLINT),
                            Column('finished_file', TEXT),
                            Column('backlog', SMALLINT),
                            Column('tmdbid', TEXT),
                            Column('alternative_titles', TEXT),
                            Column('media_release_date', TEXT),
                            Column('origin', TEXT)
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
                                   Column('download_client', TEXT),
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
        try:
            self.engine = create_engine(DB_NAME, echo=False, connect_args={'timeout': 30})
            if not os.path.isfile(core.DB_FILE):
                print('Creating database file {}'.format(core.DB_FILE))
                self.create_database(DB_NAME)
            else:
                print('Connected to database {}'.format(DB_NAME))
                self.update_tables()
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Opening SQL DB.', exc_info=True)
            raise

    def create_database(self, DB_NAME):
        ''' Creates database and recreates self.engine
        DB_NAME (str): absolute file path to database

        Does not return. DO NOT supress exceptions, this MUST succeed for Watcer to start.
        '''
        print('Creating tables.')
        self.metadata.create_all(self.engine)
        self.engine = create_engine(DB_NAME, echo=False, connect_args={'timeout': 30})
        print('Connected to database {}'.format(DB_NAME))
        return

    def execute(self, command):
        ''' Executes SQL command
        command (list): SQL commands ie ['INSERT INTO table (columns) VALUES (?)', 'value']

        We are going to loop this up to 5 times in case the database is locked.
        After each attempt we wait 1 second to try again. This allows the query
            that has the database locked to (hopefully) finish. It might
            (i'm not sure) allow a query to jump in line between a series of
            queries. So if we are writing searchresults to every movie at once,
            the get_user_movies request may be able to jump in between them to
            get the user's movies to the browser. Maybe.

        Return type will

        Returns object sqlalchemy ResultProxy of command, or None if unable to execute
        '''

        tries = 0
        while tries < 5:
            try:
                result = self.engine.execute(*command)
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
        return None

    def write(self, TABLE, DB_STRING):
        ''' Writes row to table
        TABLE (str): name of db table
        DB_STRING (dict): {columns:values} to write to TABLE

        Returns Bool
        '''

        logging.debug('Writing data to {}.'.format(TABLE))

        cols = ', '.join(DB_STRING.keys())
        vals = list(DB_STRING.values())

        qmarks = ', '.join(['?'] * len(DB_STRING))

        sql = 'INSERT INTO {} ( {} ) VALUES ( {} )'.format(TABLE, cols, qmarks)

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to write to database.')
            return False

    def write_search_results(self, LIST):
        ''' Writes search results to table
        LIST (list): dicts to write into SEARCHRESULTS

        Returns bool
        '''

        if not LIST:
            return True

        logging.debug('Writing batch into SEARCHRESULTS.')

        INSERT = self.SEARCHRESULTS.insert()

        command = [INSERT, LIST]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to write search results.')
            return False

    def update(self, TABLE, COLUMN, VALUE, idcol, idval):
        ''' Updates single value in existing table row.
        TABLE (str): name of database table to write to
        COLUMN (str): column to write into
        VALUE (str): value to write
        idcol (str): column to use to id row to write to
        idval (str): value to use to id row to write to

        Writes VALUE into COLUMN where idcol == idval

        Returns Bool.
        '''

        logging.debug('Updating {} to {} for col {}:{} in {}.'.format(COLUMN, VALUE, idcol, idval.split('&')[0], TABLE))

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
        TABLE (str): database table to access
        data (dict): key/value pairs to update in table
        imdbid (str): imdbid # of movie to update
        guid (str): guid of search result to update

        Return bool.
        '''

        if imdbid:
            idcol = 'imdbid'
            idval = imdbid
        elif guid:
            idcol = 'guid'
            idval = guid
        else:
            return False

        logging.debug('Updating {} to {} in {}.'.format(idval.split('&')[0], data, TABLE))

        columns = '{}=?'.format('=?,'.join(data.keys()))

        sql = 'UPDATE {} SET {} WHERE {}=?'.format(TABLE, columns, idcol)

        vals = tuple(list(data.values()) + [idval])

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to update database row.')
            return False

    def get_user_movies(self, sort_key='title', sort_direction='DESC', limit=-1, offset=0):
        ''' Gets user's movie from database
        sort_key (str): key to sort by
        sort_direction (str): order to sort results [ASC, DESC]
        limit (int): how many results to return
        offset (int): list index to start returning results

        If limit is -1 all results are returned (still honors offset)

        Returns list of dicts with all information in MOVIES
        '''
        sort_direction = {'ASC': 'DESC', 'DESC': 'ASC'}[sort_direction]

        logging.debug('Retrieving list of user\'s movies.')

        if sort_key == 'status':
            sort_key = '''CASE WHEN status = "Waiting" THEN 1
                               WHEN status = "Wanted" THEN 2
                               WHEN status = "Found" THEN 3
                               WHEN status = "Snatched" THEN 4
                               WHEN status = "Finished" THEN 5
                               WHEN status = "Disabled" THEN 5
                          END
                       '''

        command = 'SELECT * FROM MOVIES ORDER BY {} {}'.format(sort_key, sort_direction)

        if sort_key != 'title':
            command += ', title ASC'

        if int(offset) > 0:
            command += ' LIMIT {} OFFSET {}'.format(limit, offset)

        result = self.execute([command])

        if result:
            return [dict(i) for i in result]
        else:
            logging.error('Unable to get list of user\'s movies.')
            return []

    def get_library_count(self):
        ''' Gets count of rows in MOVIES

        Returns int
        '''

        logging.debug('Getting count of library.')

        command = ['SELECT COUNT(1) FROM MOVIES']

        result = self.execute(command)

        if result:
            x = result.fetchone()[0]
            return x
        else:
            logging.error('Unable to get count of user\'s movies.')
            return 0

    def get_movie_details(self, idcol, idval):
        ''' Returns dict of single movie details from MOVIES.
        idcol (str): identifying column
        idval (str): identifying value

        Looks through MOVIES for idcol:idval

        Returns dict of first match
        '''

        logging.debug('Retrieving details for {}.'.format(idval))

        command = ['SELECT * FROM MOVIES WHERE {}="{}"'.format(idcol, idval)]

        result = self.execute(command)

        if result:
            data = result.fetchone()
            if data:
                return dict(data)
            else:
                return {}
        else:
            return {}

    def get_search_results(self, imdbid, quality=None):
        ''' Gets all search results for a given movie
        imdbid (str): imdb id #
        quality (str): name of quality profile. Used to sort order <optional>

        Gets all search results sorted by score, then size.

        Looks at quality to determine size sort direction. If not passed defaults to
            DESC, with bigger files first.

        Returns list of dicts for all SEARCHRESULTS that match imdbid
        '''

        if quality in core.CONFIG['Quality']['Profiles'] and core.CONFIG['Quality']['Profiles'][quality]['prefersmaller']:
            sort = 'ASC'
        else:
            sort = 'DESC'

        logging.debug('Retrieving Search Results for {}.'.format(imdbid))
        TABLE = 'SEARCHRESULTS'

        command = ['SELECT * FROM {} WHERE imdbid="{}" ORDER BY score DESC, size {}, freeleech DESC'.format(TABLE, imdbid, sort)]

        results = self.execute(command)

        if results:
            res = results.fetchall()
            return [dict(i) for i in res]
        else:
            return []

    def get_marked_results(self, imdbid):
        ''' Gets all entries in MARKEDRESULTS for given movie
        imdbid (str): imdb id #

        Returns dict {guid:status, guid:status, etc}
        '''

        logging.debug('Retrieving Marked Results for {}.'.format(imdbid))

        TABLE = 'MARKEDRESULTS'

        results = {}

        command = ['SELECT * FROM {} WHERE imdbid="{}"'.format(TABLE, imdbid)]

        data = self.execute(command)

        if data:
            for i in data.fetchall():
                results[i['guid']] = i['status']

        return results

    def remove_movie(self, imdbid):
        ''' Removes movie and search results from DB
        imdbid (str): imdb id #

        Doesn't access sql directly, but instructs other methods to delete all information that matches imdbid.

        Removes from MOVIE, SEARCHRESULTS, and deletes poster. Keeps MARKEDRESULTS.

        Returns bool (True/False on success or None if movie not found)
        '''

        logging.debug('Removing {} from {}.'.format(imdbid, 'MOVIES'))

        if not self.row_exists('MOVIES', imdbid=imdbid):
            return None

        if not self.delete('MOVIES', 'imdbid', imdbid):
            return False

        logging.debug('Removing any stored search results for {}.'.format(imdbid))

        if self.row_exists('SEARCHRESULTS', imdbid):
            if not self.purge_search_results(imdbid=imdbid):
                return False

        logging.debug('{} removed.'.format(imdbid))
        return True

    def delete(self, TABLE, idcol, idval):
        ''' Deletes row where idcol == idval
        TABLE (str): table name
        idcol (str): identifying column
        idval (str): identifying value

        Returns Bool
        '''

        logging.debug('Removing from {} where {} is {}.'.format(TABLE, idcol, idval.split('&')[0]))

        command = ['DELETE FROM {} WHERE {}="{}"'.format(TABLE, idcol, idval)]

        if self.execute(command):
            return True
        else:
            return False

    def purge_search_results(self, imdbid=''):
        ''' Deletes all search results
        imdbid (str): imdb id #     <optional>

        Be careful with this one. Supplying an imdbid deletes search results for that
            movie. If you do not supply an imdbid it purges FOR ALL MOVIES.

        BE CAREFUL.

        Returns Bool
        '''

        TABLE = 'SEARCHRESULTS'

        if imdbid:
            command = ['DELETE FROM {} WHERE imdbid="{}"'.format(TABLE, imdbid)]
        else:
            command = ['DELETE FROM {}'.format(TABLE)]

        if self.execute(command):
            return True
        else:
            return False

    def get_distinct(self, TABLE, column, idcol, idval):
        ''' Gets unique values in TABLE
        TABLE (str): table name
        column (str): column to return
        idcol (str): identifying column
        idval (str): identifying value

        Gets values in TABLE:column where idcol == idval

        Returns list ['val1', 'val2', 'val3'] (list can be empty)
        '''

        logging.debug('Getting distinct values for {} in {}'.format(idval.split('&')[0], TABLE))

        command = ['SELECT DISTINCT {} FROM {} WHERE {}="{}"'.format(column, TABLE, idcol, idval)]

        data = self.execute(command)

        if data:
            data = data.fetchall()

            lst = []
            for i in data:
                lst.append(i[column])
            return lst
        else:
            logging.error('Unable to read database.')
            return []

    def row_exists(self, TABLE, imdbid='', guid='', downloadid=''):
        ''' Checks if row exists in table
        TABLE (str): name of sql table to look through
        imdbid (str): imdb identification number    <optional - see notes>
        guid (str): download guid                   <optional - see notes>
        downloadid (str): downloader id             <optional - see notes>

        Checks TABLE for imdbid, guid, or downloadid.
        Exactly one optional variable must be supplied.

        Used to check if we need to add row or update existing row.

        Returns Bool
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

        command = ['SELECT 1 FROM {} WHERE {}="{}"'.format(TABLE, idcol, idval)]

        row = self.execute(command)

        if row is False or row.fetchone() is None:
            return False
        else:
            return True

    def get_single_search_result(self, idcol, idval):
        ''' Gets single search result
        idcol (str): identifying column
        idval (str): identifying value

        Finds in SEARCHRESULTS a row where idcol == idval

        Returns dict
        '''

        logging.debug('Retrieving search result details for {}.'.format(idval.split('&')[0]))

        command = ['SELECT * FROM SEARCHRESULTS WHERE {}="{}"'.format(idcol, idval)]

        result = self.execute(command)

        if result:
            return result.fetchone()
        else:
            return {}

    def _get_existing_schema(self):
        ''' Gets existing database schema

        Expresses database schema as {TABLENAME: {COLUMN_NAME: COLUMN_TYPE}}

        Returns dict
        '''
        table_dict = {}

        # get list of tables in db:
        command = ['SELECT name FROM sqlite_master WHERE type="table"']
        tables = self.execute(command)

        table_dict = {}

        if not tables:
            return {}

        for i in tables:
            i = i[0]
            command = ['PRAGMA table_info({})'.format(i)]
            columns = self.execute(command)
            if not columns:
                continue
            tmp_dict = {}
            for col in columns:
                tmp_dict[col['name']] = col['type']
            table_dict[i] = tmp_dict

        return table_dict

    def _get_intended_schema(self):
        ''' Gets indended database schema as described in self.__init__

        Expresses database schema as {TABLENAME: {COLUMN_NAME: COLUMN_TYPE}}

        Returns dict
        '''

        d = {}
        for table in self.metadata.tables.keys():
            selftable = getattr(self, table)
            d2 = {}
            for i in selftable.c:
                d2[i.name] = str(i.type)
            d[table] = d2
        return d

    def update_tables(self):
        ''' Updates database tables

        Adds new rows to table based on diff between intended and existing schema

        Also includes other methods required to manipulate database on startup

        Returns Bool
        '''

        for i in self.get_user_movies():
            p = i['poster']
            if p and 'poster/' in p:
                self.update('MOVIES', 'poster', p.replace('poster/', 'posters/'), 'imdbid', i['imdbid'])

        existing = self._get_existing_schema()
        intended = self._get_intended_schema()

        diff = Comparisons.compare_dict(intended, existing)

        if not diff:
            return True

        print('Database update required. This may take some time.')

        backup_dir = os.path.join(core.PROG_PATH, 'db')
        logging.debug('Backing up database to {}.'.format(backup_dir))
        print('Backing up database to {}.'.format(backup_dir))
        try:
            if not os.path.isdir(backup_dir):
                os.mkdir(backup_dir)
            backup_name = 'watcher.sqlite.{}'.format(datetime.date.today())

            shutil.copyfile(core.DB_FILE, os.path.join(backup_dir, backup_name))
        except Exception as e:
            print('Error backing up database.')
            logging.error('Copying SQL DB.', exc_info=True)
            raise

        logging.debug('Modifying database tables.')
        print('Modifying tables.')

        '''
        For each item in diff, create new column.
        Then, if the new columns name is in SQL.convert_names, copy data from old column
        Create the new table, then copy data from TMP table
        '''
        for table, schema in diff.items():
            if table not in existing:
                logging.debug('Creating table {}'.format(table))
                print('Creating table {}'.format(table))
                getattr(self, table).create(self.engine)
                continue
            logging.debug('Modifying table {}.'.format(table))
            print('Modifying table {}'.format(table))
            for name, kind in schema.items():
                command = ['ALTER TABLE {} ADD COLUMN {} {}'.format(table, name, kind)]

                self.execute(command)

                if table in SQL.convert_names.keys():
                    for pair in SQL.convert_names[table]:
                        if pair[0] == name:
                            command = ['UPDATE {} SET {} = {}'.format(table, pair[0], pair[1])]
                            self.execute(command)

            # move TABLE to TABLE_TMP
            table_tmp = '{}_TMP'.format(table)
            logging.debug('Renaming table to {}.'.format(table_tmp))
            print('Renaming table to {}'.format(table_tmp))
            command = ['ALTER TABLE {} RENAME TO {}'.format(table, table_tmp)]
            self.execute(command)

            # create new table
            logging.debug('Creating new table {}.'.format(table))
            print('Creating new table {}'.format(table))
            table_meta = getattr(self, table)
            table_meta.create(self.engine)

            # copy data over
            logging.debug('Merging data from {} to {}.'.format(table_tmp, table))
            print('Merging data from {} to {}'.format(table_tmp, table))
            names = ', '.join(intended[table].keys())
            command = ['INSERT INTO {} ({}) SELECT {} FROM {}'.format(table, names, names, table_tmp)]
            self.execute(command)

            logging.debug('Dropping table {}.'.format(table_tmp))
            print('Dropping table {}'.format(table_tmp))
            command = ['DROP TABLE {}'.format(table_tmp)]
            self.execute(command)

            logging.debug('Finished updating table {}.'.format(table))
            print('Finished updating table {}'.format(table))

        logging.debug('Database updated')
        print('Database updated.')

    def torznab_caps(self, url):
        ''' Gets caps list for torznab providers
        url (str): url of torznab indexer

        Returns list of caps ie ['q', 'imdbid'] or []
        '''

        logging.debug('Retreiving caps for {}'.format(url))

        command = ['SELECT "caps" FROM CAPS WHERE url="{}"'.format(url)]

        row = self.execute(command)
        caps = row.fetchone()
        if caps is None:
            return []
        else:
            return caps[0].split(',')

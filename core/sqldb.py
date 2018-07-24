import core
import datetime
import logging
import time
import os
import shutil

from core.helpers import Comparisons
import sqlalchemy as sqla

logging = logging.getLogger(__name__)

current_version = 9


def proxy_to_dict(p):
    ''' Conversts sqla resultproxy to dict
    p (resultproxy): response from sqla call

    returns list of dicts
    '''
    return [dict(i) for i in p]


class SQL(object):
    '''
    Class to handle all database interactions

    SQL.convert_names is used to convert column names in a table.
        This should be formatted as {TABLE: [(new_column, old_column)],
                                     TABLE2: [(new_column, old_column), (new_column_2, old_column_2)]
                                     }

    '''

    convert_names = {'MOVIES':
                     [('url', 'tomatourl'),
                      ('score', 'tomatorating'),
                      ('release_date', 'released'),
                      ('finished_date', 'finisheddate'),
                      ('media_release_date', 'digital_release_date')]
                     }

    def __init__(self):
        self.metadata = sqla.MetaData()
        DB_NAME = 'sqlite:///{}'.format(core.DB_FILE)

        # These definitions only exist to CREATE tables.
        self.MOVIES = sqla.Table('MOVIES', self.metadata,
                                 sqla.Column('added_date', sqla.TEXT),
                                 sqla.Column('imdbid', sqla.TEXT),
                                 sqla.Column('title', sqla.TEXT),
                                 sqla.Column('year', sqla.TEXT),
                                 sqla.Column('poster', sqla.TEXT),
                                 sqla.Column('plot', sqla.TEXT),
                                 sqla.Column('url', sqla.TEXT),
                                 sqla.Column('score', sqla.TEXT),
                                 sqla.Column('release_date', sqla.TEXT),
                                 sqla.Column('rated', sqla.TEXT),
                                 sqla.Column('status', sqla.TEXT),
                                 sqla.Column('predb_backlog', sqla.TEXT),
                                 sqla.Column('predb', sqla.TEXT),
                                 sqla.Column('quality', sqla.TEXT),
                                 sqla.Column('finished_date', sqla.TEXT),
                                 sqla.Column('finished_score', sqla.SMALLINT),
                                 sqla.Column('finished_file', sqla.TEXT),
                                 sqla.Column('backlog', sqla.SMALLINT),
                                 sqla.Column('tmdbid', sqla.TEXT),
                                 sqla.Column('alternative_titles', sqla.TEXT),
                                 sqla.Column('media_release_date', sqla.TEXT),
                                 sqla.Column('origin', sqla.TEXT),
                                 sqla.Column('sort_title', sqla.TEXT),
                                 sqla.Column('filters', sqla.TEXT)
                                 )
        self.SEARCHRESULTS = sqla.Table('SEARCHRESULTS', self.metadata,
                                        sqla.Column('score', sqla.SMALLINT),
                                        sqla.Column('size', sqla.SMALLINT),
                                        sqla.Column('status', sqla.TEXT),
                                        sqla.Column('pubdate', sqla.TEXT),
                                        sqla.Column('title', sqla.TEXT),
                                        sqla.Column('imdbid', sqla.TEXT),
                                        sqla.Column('indexer', sqla.TEXT),
                                        sqla.Column('date_found', sqla.TEXT),
                                        sqla.Column('info_link', sqla.TEXT),
                                        sqla.Column('guid', sqla.TEXT),
                                        sqla.Column('torrentfile', sqla.TEXT),
                                        sqla.Column('resolution', sqla.TEXT),
                                        sqla.Column('type', sqla.TEXT),
                                        sqla.Column('downloadid', sqla.TEXT),
                                        sqla.Column('download_client', sqla.TEXT),
                                        sqla.Column('freeleech', sqla.SMALLINT)
                                        )
        self.MARKEDRESULTS = sqla.Table('MARKEDRESULTS', self.metadata,
                                        sqla.Column('imdbid', sqla.TEXT),
                                        sqla.Column('guid', sqla.TEXT),
                                        sqla.Column('status', sqla.TEXT)
                                        )
        self.CAPS = sqla.Table('CAPS', self.metadata,
                               sqla.Column('url', sqla.TEXT),
                               sqla.Column('caps', sqla.TEXT)
                               )
        self.TASKS = sqla.Table('TASKS', self.metadata,
                                sqla.Column('name', sqla.TEXT),
                                sqla.Column('last_execution', sqla.TEXT)
                                )
        self.SYSTEM = sqla.Table('SYSTEM', self.metadata,
                                 sqla.Column('name', sqla.TEXT, primary_key=True),
                                 sqla.Column('data', sqla.TEXT)
                                 )

        try:
            self.engine = sqla.create_engine(DB_NAME, echo=False, connect_args={'timeout': 30})
            if not os.path.isfile(core.DB_FILE):
                print('Creating database file {}'.format(core.DB_FILE))
                self.create_database(DB_NAME)
            else:
                logging.info('Connected to database {}'.format(DB_NAME))
                print('Connected to database {}'.format(DB_NAME))

        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Opening SQL DB.', exc_info=True)
            raise

    def create_database(self, DB_NAME):
        ''' Creates database and recreates self.engine
        DB_NAME (str): absolute file path to database

        Does not return. DO NOT supress exceptions, this MUST succeed for Watcher to start.
        '''
        logging.info('Creating Database tables.')
        print('Creating tables.')
        self.metadata.create_all(self.engine)
        self.engine = sqla.create_engine(DB_NAME, echo=False, connect_args={'timeout': 30})
        self.set_version(current_version)
        logging.info('Connected to database {}'.format(DB_NAME))
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

        Returns object sqlalchemy ResultProxy of command, or None if unable to execute
        '''

        logging.debug('Executing SQL command: {}'.format(command))

        tries = 0
        while tries < 5:
            try:
                return self.engine.execute(*command)

            except Exception as e:
                logging.error('SQL Database Query: {}.'.format(command), exc_info=True)
                if 'database is locked' in e.args[0]:
                    logging.debug('SQL Query attempt # {}.'.format(tries))
                    tries += 1
                    time.sleep(1)
                else:
                    logging.error('SQL Databse Query: {}.'.format(command), exc_info=True)
                    return None
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

        logging.debug('Updating {} to {} for rows that match {}:{} in {}.'.format(COLUMN, VALUE, idcol, idval.split('&')[0], TABLE))

        sql = 'UPDATE {} SET {}=? WHERE {}=?'.format(TABLE, COLUMN, idcol)
        vals = (VALUE, idval)

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to update database row.')
            return False

    def update_multiple_values(self, TABLE, data, idcol, idval):
        ''' Updates mulitple values in a single sql row
        TABLE (str): database table to access
        data (dict): key/value pairs to update in table
        idcol (str): column to use to id row to write to
        idval (str): value to use to id row to write to

        Return bool.
        '''

        logging.debug('Updating {}:{} to {} in {}.'.format(idcol, idval.split('&')[0], data, TABLE))

        columns = '{}=?'.format('=?,'.join(data.keys()))

        sql = 'UPDATE {} SET {} WHERE {}=?'.format(TABLE, columns, idcol)

        vals = tuple(list(data.values()) + [idval])

        command = [sql, vals]

        if self.execute(command):
            return True
        else:
            logging.error('Unable to update database row.')
            return False

    def update_multiple_rows(self, TABLE, values, id_col):
        ''' Update multiple rows in a single table
        TABLE (str): database table to access
        values (list): of dicts of identifier and update values
        id_col (str): name of column in values used to identify row

        Values must be a list of dictionaries with k:v pairs reprenting columns names and
            data to write to that column. It must also contain an indentifying k:v that
            matches the column passed in id_col.

            For example:

            update_multiple_rows('MOVIES', [{'year': 2000, 'rated': 'R'}, {'year': 1990, 'rated': 'PG-13'}], 'year')

            This call will update all MOVIES rows where 'year' == 2000 and set 'rated' to 'R', and update all MOVIES
                rows where 'year' == 1990 and set 'rated' to 'PG-13'

        id_col and corresponding 'values' keys will be changed to '{}_'.format(id_col) to make it compatible with sqlalchemy

        Returns Bool
        '''

        if id_col not in values[0].keys():
            logging.error('id_col not in values.')
            return False

        id_col_ = '{}_'.format(id_col)

        for d in values:
            d[id_col_] = d[id_col]

        write = {k: sqla.bindparam(k) for k in values[0].keys() if k != id_col_}

        TABLE = getattr(core.sql, TABLE)

        core.sql.engine.execute(TABLE.update().where(getattr(TABLE.c, id_col) == sqla.bindparam(id_col_)).values(write), values)

        return

    def get_user_movies(self, sort_key='title', sort_direction='DESC', limit=-1, offset=0, hide_finished=False):
        ''' Gets user's movie from database
        sort_key (str): key to sort by
        sort_direction (str): order to sort results [ASC, DESC]
        limit (int): how many results to return
        offset (int): list index to start returning results
        hide_finished (bool): return

        If limit is -1 all results are returned (still honors offset)

        Returns list of dicts with all information in MOVIES
        '''
        sort_direction = {'ASC': 'DESC', 'DESC': 'ASC'}[sort_direction]

        logging.debug('Retrieving list of user\'s movies.')

        filters = 'WHERE status NOT IN ("Finished", "Disabled")' if hide_finished else ''

        if sort_key == 'status':
            sort_key = '''CASE WHEN status = "Waiting" THEN 1
                               WHEN status = "Wanted" THEN 2
                               WHEN status = "Found" THEN 3
                               WHEN status = "Snatched" THEN 4
                               WHEN status = "Finished" THEN 5
                               WHEN status = "Disabled" THEN 5
                          END
                       '''

        command = 'SELECT * FROM MOVIES {} ORDER BY {} {}'.format(filters, sort_key, sort_direction)

        command += ', sort_title ASC' if sort_key != 'sort_title' else ''

        if int(limit) > 0:
            command += ' LIMIT {} OFFSET {}'.format(limit, offset)

        result = self.execute([command])

        if result:
            return proxy_to_dict(result)
        else:
            logging.error('Unable to get list of user\'s movies.')
            return []

    def get_library_count(self):
        ''' Gets count of rows in MOVIES
        Gets total count and Finished count

        Returns tuple (int, int)
        '''

        logging.debug('Getting count of library.')

        result = self.execute(['SELECT COUNT(1) FROM MOVIES'])
        if result:
            c = result.fetchone()[0]
        else:
            logging.error('Unable to get count of user\'s movies.')
            return (0, 0)

        result = self.execute(['SELECT COUNT(1) FROM MOVIES WHERE status IN ("Finished", "Disabled")'])
        if result:
            f = result.fetchone()[0]
        else:
            logging.error('Unable to get count of user\'s movies.')
            return (0, 0)

        return (c, f)

    def get_movie_details(self, idcol, idval):
        ''' Returns dict of single movie details from MOVIES.
        idcol (str): identifying column
        idval (str): identifying value

        Looks through MOVIES for idcol:idval

        Returns dict of first match
        '''

        logging.debug('Retrieving details for movie {}.'.format(idval))

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

        logging.debug('Retrieving Search Results for {}.'.format(imdbid))

        if quality in core.CONFIG['Quality']['Profiles'] and core.CONFIG['Quality']['Profiles'][quality]['prefersmaller']:
            sort = 'ASC'
        else:
            sort = 'DESC'

        if core.CONFIG['Search']['preferredsource'] == '':
            sk = ''
        else:
            sk = ''', CASE type WHEN "nzb" THEN 0
                                WHEN "torrent" THEN 1
                                WHEN "magnet" THEN 1
                    END {}
                '''.format('ASC' if core.CONFIG['Search']['preferredsource'] == 'usenet' else 'DESC')

        command = ['SELECT * FROM SEARCHRESULTS WHERE imdbid="{}" ORDER BY score DESC {}, size {}, freeleech DESC'.format(imdbid, sk, sort)]

        results = self.execute(command)

        if results:
            return proxy_to_dict(results.fetchall())
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

        logging.debug('Removing {} from database.'.format(imdbid))

        if not self.row_exists('MOVIES', imdbid=imdbid):
            return None

        if not self.delete('MOVIES', 'imdbid', imdbid):
            return False

        if self.row_exists('SEARCHRESULTS', imdbid=imdbid):
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

        if imdbid:
            logging.debug('Purging search results for {}'.format(imdbid))
            command = ['DELETE FROM SEARCHRESULTS WHERE imdbid="{}"'.format(imdbid)]
        else:
            logging.debug('Purging search results for all movies.')
            command = ['DELETE FROM SEARCHRESULTS']

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

        Currently not used, but kept for future reference
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

    def row_exists(self, TABLE, **cols):
        ''' Checks if row exists in table
        TABLE (str): name of sql table to look through
        cols (kwargs): idcol/idval to find in table.

        Checks if any row exists in table where all idcol == idval.

        Used to check if we need to add row or update existing row.

        Returns Bool
        '''

        matches = ['{}="{}"'.format(k, v) for k, v in cols.items()]

        logging.debug('Checking if {} exists in database table {}'.format(','.join(matches), TABLE))

        command = ['SELECT 1 FROM {} WHERE {}'.format(TABLE, ' AND '.join(matches))]

        row = self.execute(command)

        if not row or row.fetchone() is None:
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

        command = ['SELECT * FROM SEARCHRESULTS WHERE {}="{}" ORDER BY score DESC, size DESC'.format(idcol, idval)]

        result = self.execute(command)

        if result:
            data = result.fetchone()
            if data:
                return dict(data)
        return {}

    def _get_existing_schema(self):
        ''' Gets existing database schema

        Expresses database schema as {TABLENAME: {COLUMN_NAME: COLUMN_TYPE}}

        Returns dict
        '''
        logging.debug('Getting existing database schema.')
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
        logging.debug('Getting intended database schema.')

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

        Returns Bool, but should crash program if an exception is thrown. DO NOT CATCH EXCEPTIONS
        '''

        logging.info('Checking if database needs to be updated.')

        existing = self._get_existing_schema()
        intended = self._get_intended_schema()

        diff = Comparisons.compare_dict(intended, existing)

        if not diff:
            return True

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

            return True

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

    def version(self):
        ''' Get user_version of sql database

        Returns int of db version
        '''
        return self.execute(['PRAGMA user_version']).fetchone()[0]

    def set_version(self, v):
        ''' Set user_version of sql database
        v (int): version of database to set

        Does not return
        '''
        self.execute(['PRAGMA user_version = {}'.format(v)])

    def update_database(self):
        ''' Handles database updates
        '''
        v = self.version()
        if v >= current_version:
            return

        print('Database update required. This may take some time.')
        logging.info('Updating database to version {}.'.format(current_version))

        backup_dir = os.path.join(core.PROG_PATH, 'db')
        logging.debug('Backing up database to {}.'.format(backup_dir))
        print('Backing up database to {}.'.format(backup_dir))
        try:
            if not os.path.isdir(backup_dir):
                os.mkdir(backup_dir)
            backup_name = '{}.backup-{}'.format(core.DB_FILE, datetime.date.today())

            shutil.copyfile(core.DB_FILE, os.path.join(backup_dir, backup_name))
        except Exception as e:
            print('Error backing up database.')
            logging.error('Copying SQL DB.', exc_info=True)
            raise

        for i in range(v + 1, current_version + 1):
            logging.info('Executing Database Update {}'.format(i))
            print('Executing database update {}'.format(i))
            m = getattr(DatabaseUpdate, 'update_{}'.format(i))
            m()

        self.set_version(current_version)

    def dump(self, table):
        ''' Dump entire table as dict
        table (str): name of table to dump

        Gets table contents without sorting, fitlering, etc so it can't
            fail by asking for a column that might not exist yet.

        Returns list of dicts
        '''
        return proxy_to_dict(self.execute(['SELECT * FROM {}'.format(table)]))

    def system(self, name):
        ''' Gets 'data' column from SYSTEM table for name
        name (str): identify row to return 'data' column from

        Returns str
        '''

        cmd = 'SELECT data FROM SYSTEM WHERE name="{}"'.format(name)

        result = self.execute([cmd])

        if result:
            return result.fetchone()[0]
        else:
            return None

    def quick_titles(self):
        ''' Gets titles and ids from library

        Gets a simple tuple of (title, tmdbid, imdbid) for every movie in MOVIES

        Returns list of tuples
        '''

        logging.debug('Retrieving random movie id')

        command = ['SELECT title, tmdbid, imdbid FROM MOVIES ORDER BY sort_title']

        result = self.execute(command)

        return [tuple(i) for i in result.fetchall()] if result else []


class DatabaseUpdate(object):
    ''' namespace for database update methods
    There is one method for each database version. These methods are NOT
        cumulative and MUST be executed in order.

    Methods should be formatted as such:

    @staticmethod
    def update_<i>():

        d = core.sql.dump(<TABLE>)
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')

            <do something>

        print()

    '''

    @staticmethod
    def update_0():
        pass

    @staticmethod
    def update_1():
        ''' Correct posters column in MOVIES
        Change 'poster/' to 'posters/' in file path
        '''

        d = core.sql.dump('MOVIES')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            p = i['poster']
            if p and 'poster/' in p:
                core.sql.update('MOVIES', 'poster', p.replace('poster/', 'posters/'), 'imdbid', i['imdbid'])
        print()

    @staticmethod
    def update_2():
        ''' Add sort_titles column in MOVIES
        sort_title is like title, but with articles placed at the end
            ie: The Movie Name is Movie Name, The

        Populates column with titles
        '''
        core.sql.update_tables()

        values = []

        d = core.sql.dump('MOVIES')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            t = i['title']
            if t.startswith('The '):
                t = t[4:] + ', The'
            elif t.startswith('A '):
                t = t[2:] + ', A'
            elif t.startswith('An '):
                t = t[3:] + ', An'

            values.append({'imdbid': i['imdbid'], 'sort_title': t})

        if values:
            core.sql.update_multiple_rows('MOVIES', values, 'imdbid')
        print()

    @staticmethod
    def update_3():
        ''' Clean up search results missing imdbid field '''

        d = core.sql.dump('SEARCHRESULTS')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            if not i.get('imdbid') and i.get('guid'):
                core.sql.delete('SEARCHRESULTS', 'guid', i['guid'])
        print()

    @staticmethod
    def update_4():
        ''' Change MOVIES field 'poster' to just [imdbid].jpg '''
        values = []

        d = core.sql.dump('MOVIES')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            if i['poster']:
                p = i['poster'].split('/')[-1]
                values.append({'imdbid': i['imdbid'], 'poster': p})

        if values:
            core.sql.update_multiple_rows('MOVIES', values, 'imdbid')
        print()

    @staticmethod
    def update_5():
        ''' Add TASKS table '''
        core.sql.update_tables()

    @staticmethod
    def update_6():
        ''' Add SYSTEM table and imdb_sync_record'''
        core.sql.update_tables()
        core.sql.write('SYSTEM', {'name': 'imdb_sync_record', 'data': '{}'})

    @staticmethod
    def update_7():
        ''' Fix missing 'tt' in imdbid column of SEARCHRESULTS '''
        values = []

        d = core.sql.dump('SEARCHRESULTS')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            if i['imdbid'] and not i['imdbid'].startswith('tt'):
                n = 'tt' + i['imdbid']
                values.append({'imdbid': n, 'guid': i['guid']})
        if values:
            core.sql.update_multiple_rows('SEARCHRESULTS', values, 'guid')
        print()

    @staticmethod
    def update_8():
        ''' Add filters column to MOVIES '''
        core.sql.update_tables()

    @staticmethod
    def update_9():
        values = []

        d = core.sql.dump('MOVIES')
        l = len(d)

        for ind, i in enumerate(d):
            print('{}%\r'.format(int((ind + 1) / l * 100)), end='')
            if not i['filters']:
                values.append({'imdbid': i['imdbid'], 'filters': '{"preferredwords": "", "requiredwords": "", "ignoredwords": ""}'})
        if values:
            core.sql.update_multiple_rows('MOVIES', values, 'imdbid')
        print()

    # Adding a new method? Remember to update the current_version #

import logging
import datetime

from base64 import b16encode
import json
import core
from core.helpers import Url

logging = logging.getLogger(__name__)


class Score():

    def score(self, results, imdbid=None, imported=False):
        ''' Scores and filters search results.
        results (list): dicts of search results
        imdbid (str): imdb identification number                    <optional - default None>
        impored (bool): indicate if search result is faked import   <optional - default False>

        If imported is True imdbid can be ignored. Otherwise imdbid is required.

        If imported, uses modified 'Default' quality profile so results
            cannot be filtered out.

        Iterates over the list and filters movies based on Words.
        Scores movie based on reslution priority, title match, and
            preferred words,

        Word groups are split in to a list of lists:
        [['word'], ['word2', 'word3'], 'word4']

        Adds 'score' key to each dict in results and applies score.

        Returns list of result dicts
        '''

        logging.info('Scoring {} search results.'.format(len(results)))

        if imdbid is None and imported is False:
            logging.warning('Imdbid required if result is not library import.')
            return results

        self.results = results
        year = None

        if imported:
            logging.debug('Search results are Imports, using custom Default quality profile.')
            titles = []
            check_size = False
            movie_details = {'year': '\n'}
            quality = self.import_quality()
        else:
            movie_details = core.sql.get_movie_details('imdbid', imdbid)
            year = movie_details.get('year')
            quality_profile = movie_details['quality']
            logging.debug('Scoring based on quality profile {}'.format(quality_profile))

            titles = [movie_details['title']]
            if movie_details['alternative_titles']:
                titles += movie_details['alternative_titles'].split(',')

            check_size = True
            if quality_profile in core.CONFIG['Quality']['Profiles']:
                quality = core.CONFIG['Quality']['Profiles'][quality_profile]
            else:
                quality = core.CONFIG['Quality']['Profiles']['Default']

        sources = quality['Sources']
        retention = core.CONFIG['Search']['retention']
        seeds = core.CONFIG['Search']['mintorrentseeds']

        required = [i.split('&') for i in quality['requiredwords'].lower().replace(' ', '').split(',') if i != '']
        preferred = [i.split('&') for i in quality['preferredwords'].lower().replace(' ', '').split(',') if i != '']
        ignored = [i.split('&') for i in quality['ignoredwords'].lower().replace(' ', '').split(',') if i != '']

        # These all just modify self.results
        self.reset()
        self.remove_ignored(ignored)
        self.keep_required(required)
        self.retention_check(retention)
        self.seed_check(seeds)
        self.freeleech(core.CONFIG['Search']['freeleechpoints'])
        self.score_sources(sources, check_size=check_size)
        if quality['scoretitle']:
            self.fuzzy_title(titles, year=year)
        self.score_preferred(preferred)
        logging.info('Finished scoring search results.')

        return self.results

    def reset(self):
        ''' Sets all result's scores to 0 '''
        logging.debug('Resetting release scores to 0.')
        for i, d in enumerate(self.results):
            self.results[i]['score'] = 0

    def remove_ignored(self, group_list):
        ''' Remove results with ignored groups of 'words'
        group_list (list): forbidden groups of words

        group_list must be formatted as a list of lists ie:
            [['word1'], ['word2', 'word3']]

        Iterates through self.results and removes every entry that contains any
            group of words in group_list

        Does not return
        '''

        keep = []

        if not group_list or group_list == ['']:
            return

        logging.info('Filtering Ignored Words.')
        for r in self.results:
            if r['type'] == 'import' and r not in keep:
                keep.append(r)
                continue
            cond = False
            for word_group in group_list:
                if all(word in r['title'].lower() for word in word_group):
                    logging.debug('{} found in {}, removing from search results.'.format(word_group, r['title']))
                    cond = True
                    break
            if cond is False and r not in keep:
                keep.append(r)

        self.results = keep
        logging.info('Keeping {} results.'.format(len(self.results)))

    def keep_required(self, group_list):
        ''' Remove results without required groups of 'words'
        group_list (list): required groups of words

        group_list must be formatted as a list of lists ie:
            [['word1'], ['word2', 'word3']]

        Iterates through self.results and removes every entry that does not
            contain any group of words in group_list

        Does not return
        '''

        keep = []

        if not group_list or group_list == ['']:
            return

        logging.info('Filtering Required Words.')
        for r in self.results:
            if r['type'] == 'import' and r not in keep:
                keep.append(r)
                continue
            for word_group in group_list:
                if all(word in r['title'].lower() for word in word_group) and r not in keep:
                    logging.debug('{} found in {}, keeping this search result.'.format(word_group, r['title']))
                    keep.append(r)
                    break
                else:
                    continue

        self.results = keep
        logging.info('Keeping {} results.'.format(len(self.results)))

    def retention_check(self, retention):
        ''' Remove results older than 'retention' days
        retention (int): days of retention limit

        Iterates through self.results and removes any nzb entry that was
            published more than 'retention' days ago

        Does not return
        '''

        today = datetime.datetime.today()

        if retention == 0:
            return

        logging.info('Checking retention.')
        lst = []
        for result in self.results:
            if result['type'] != 'nzb':
                lst.append(result)
            else:
                pubdate = datetime.datetime.strptime(result['pubdate'], '%d %b %Y')
                age = (today - pubdate).days
                if age < retention:
                    lst.append(result)
                else:
                    logging.debug('{} published {} days ago, removing search result.'.format(result['title'], age))

        self.results = lst
        logging.info('Keeping {} results.'.format(len(self.results)))

    def seed_check(self, seeds):
        ''' Remove any torrents with fewer than 'seeds' seeders
        seeds (int): Minimum number of seeds required

        Does not return
        '''

        if seeds == 0:
            return
        logging.info('Checking torrent seeds.')
        lst = []
        for result in self.results:
            if result['type'] not in ('torrent', 'magnet'):
                lst.append(result)
            else:
                if int(result['seeders']) >= seeds:
                    lst.append(result)
                else:
                    logging.debug('{} has {} seeds, removing search result.'.format(result['title'], result['seeders']))
        self.results = lst
        logging.info('Keeping {} results.'.format(len(self.results)))

    def freeleech(self, points):
        ''' Adds points to freeleech torrents
        points (int): points to add to search result

        Does not return
        '''
        logging.info('Adding Freeleech points.')
        for res in self.results:
            if res['freeleech'] == 1:
                logging.debug('Adding {} points to {}.'.format(points, res['title']))
                res['score'] += points

    def score_preferred(self, group_list):
        ''' Increase score for each group of 'words' match
        group_list (list): preferred groups of words

        group_list must be formatted as a list of lists ie:
            [['word1'], ['word2', 'word3']]

        Iterates through self.results and adds 10 points to every
            entry for each word group it contains

        Does not return
        '''

        logging.info('Scoring Preferred Words.')

        if not group_list or group_list == ['']:
            return

        for r in self.results:
            for word_group in group_list:
                if all(word in r['title'].lower() for word in word_group):
                    logging.debug('{} found in {}, adding 10 points.'.format(word_group, r['title']))
                    r['score'] += 10
                else:
                    continue

    def fuzzy_title(self, titles, year='\n'):
        ''' Score and remove results based on title match
        titles (list): titles to match against
        year (str): year of movie release           <optional - Default '\n'>

        If titles is an empty list every result is treated as a perfect match
        Matches releases based on release_title.split(year)[0]. If year is not passed,
            matches on '\n', which will include the entire string.

        Iterates through self.results and removes any entry that does not
            fuzzy match 'title' > 70.
        Adds fuzzy_score / 20 points to ['score']

        Does not return
        '''

        logging.info('Checking title match.')

        lst = []
        if titles == []:
            logging.debug('No titles available to compare, scoring all as perfect match.')
            for result in self.results:
                result['score'] += 20
                lst.append(result)
        else:
            for result in self.results:
                if result['type'] == 'import' and result not in lst:
                    logging.debug('{} is an Import, soring as a perfect match.'.format(result['title']))
                    result['score'] += 20
                    lst.append(result)
                    continue

                logging.debug('Comparing release {} with titles {}.'.format(result['title'], titles))
                matches = [self._fuzzy_title(result['title'].split(year)[0], title) for title in titles]
                if any(match > 70 for match in matches):
                    result['score'] += int(max(matches) / 5)
                    lst.append(result)
                else:
                    logging.debug('{} best title match was {}%, removing search result.'.format(result['title'], max(matches)))
        self.results = lst
        logging.info('Keeping {} results.'.format(len(self.results)))

    def _fuzzy_title(self, a, b):
        ''' Determines how much of a is in b
        a (str): String to match against b
        b (str): String to match a against

        Order of a and b matters.

        A is broken down and words are compared against B's words.

        ie:
        _fuzzy_title('This is string a', 'This is string b and has extra words.')
        Returns 75 since 75% of a is in b.

        Returns int
        '''

        a = a.replace('&', 'and')
        b = b.replace('&', 'and')

        a_words = Url.normalize(a).split(' ')
        b_words = Url.normalize(b).split(' ')

        m = 0
        a_len = len(a_words)

        for i in a_words:
            if i in b_words:
                b_words.remove(i)
                m += 1

        return int((m / a_len) * 100)

    def score_sources(self, sources, check_size=True):
        ''' Score releases based on quality/source preferences
        sources (dict): sources from user config
        check_size (bool): whether or not to filter based on size

        Iterates through self.results and removes any entry that does not
            fit into quality criteria (source-resoution, filesize)
        Adds to ['score'] based on priority of match

        Does not return
        '''

        logging.info('Filtering resolution and size requirements.')
        score_range = len(core.SOURCES) + 1

        sizes = core.CONFIG['Quality']['Sources']

        lst = []
        for result in self.results:
            result_res = result['resolution']
            logging.debug('Scoring and filtering {} based on resolution {}.'.format(result['title'], result_res))
            size = result['size'] / 1000000
            if result['type'] == 'import' and result['resolution'] not in sources:
                lst.append(result)
                continue

            for k, v in sources.items():
                if v[0] is False and result['type'] != 'import':
                    continue
                priority = v[1]
                if check_size:
                    min_size = sizes[k]['min']
                    max_size = sizes[k]['max']
                else:
                    min_size = 0
                    max_size = Ellipsis

                if result_res == k:
                    logging.debug('{} matches source {}, checking size.'.format(result['title'], k))

                    if result['type'] != 'import' and not (min_size < size < max_size):
                        logging.debug('Removing {}, size {} not in range {}-{}.'.format(result['title'], size, min_size, max_size))
                        break

                    result['score'] += abs(priority - score_range) * 40
                    lst.append(result)
                else:
                    continue

        self.results = lst
        logging.info('Keeping {} results.'.format(len(self.results)))

    def import_quality(self):
        ''' Creates quality profile for imported results

        Creates import profile that mimics Default profile, but it incapable
            of removing search results.

        Returns dict
        '''
        profile = json.loads(json.dumps(core.CONFIG['Quality']['Profiles']['Default']))

        profile['ignoredwords'] = ''
        profile['requiredwords'] = ''

        for i in profile['Sources']:
            profile['Sources'][i][0] = True

        return profile


def generate_simulacrum(movie):
    ''' Generates phony search result for imported movies
    movie (dict): movie info

    movie will use 'release_title' key if found, else 'title' to generate results

    Resturns dict to match SEARCHRESULTS table
    '''

    logging.info('Creating "fake" search result for imported movie {}'.format(movie['title']))

    result = {'status': 'Finished',
              'info_link': '#',
              'pubdate': None,
              'title': None,
              'imdbid': movie['imdbid'],
              'torrentfile': None,
              'indexer': 'Library Import',
              'date_found': str(datetime.date.today()),
              'score': None,
              'type': 'import',
              'downloadid': None,
              'guid': None,
              'resolution': movie.get('resolution'),
              'size': movie.get('size') or 0,
              'releasegroup': movie.get('releasegroup') or '',
              'freeleech': 0
              }

    title = '{}.{}.{}.{}.{}.{}'.format(movie['title'],
                                       movie['year'],
                                       movie.get('resolution') or '.',  # Kind of a hacky way to make sure it doesn't print None in the title
                                       movie.get('audiocodec') or '.',
                                       movie.get('videocodec') or '.',
                                       movie.get('releasegroup') or '.'
                                       )

    while len(title) > 0 and title[-1] == '.':
        title = title[:-1]

    while '..' in title:
        title = title.replace('..', '.')

    result['title'] = title

    result['guid'] = movie.get('guid') or 'IMPORT{}'.format(b16encode(title.encode('ascii', errors='ignore')).decode('utf-8').zfill(16)[:16])

    return result

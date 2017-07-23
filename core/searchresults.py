import logging
import datetime

from base64 import b16encode
import json
import core
from core.helpers import Url
from fuzzywuzzy import fuzz

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

        if imdbid is None and imported is False:
            logging.warning('Imdbid required if result is not library import.')
            return results

        self.results = results

        if imported is False:
            movie_details = core.sql.get_movie_details('imdbid', imdbid)
            quality_profile = movie_details['quality']

            titles = (movie_details['alternative_titles'] or '').split(',') + [movie_details['title']]
            check_size = True
            if quality_profile in core.CONFIG['Quality']['Profiles']:
                quality = core.CONFIG['Quality']['Profiles'][quality_profile]
            else:
                quality = core.CONFIG['Quality']['Profiles']['Default']
        else:
            titles = []
            check_size = False
            quality = self.import_quality()

        sources = quality['Sources']
        retention = core.CONFIG['Search']['retention']
        seeds = core.CONFIG['Search']['mintorrentseeds']

        required = [i.split('&') for i in quality['requiredwords'].lower().replace(' ', '').split(',') if i != '']
        preferred = [i.split('&') for i in quality['preferredwords'].lower().replace(' ', '').split(',') if i != '']
        ignored = [i.split('&') for i in quality['ignoredwords'].lower().replace(' ', '').split(',') if i != '']

        logging.info('Scoring {} results.'.format(len(self.results)))

        # These all just modify self.results
        self.reset()
        self.remove_ignored(ignored)
        self.keep_required(required)
        self.retention_check(retention)
        self.seed_check(seeds)
        self.freeleech(core.CONFIG['Search']['freeleechpoints'])
        self.score_sources(sources, check_size=check_size)
        if quality['scoretitle']:
            self.fuzzy_title(titles)
        self.score_preferred(preferred)
        logging.info('Finished scoring search results.')
        return self.results

    def reset(self):
        ''' Sets all result's scores to 0 '''
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
        for res in self.results:
            if res['freeleech'] == 1:
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

    def fuzzy_title(self, titles):
        ''' Score and remove results based on title match
        titles (list): titles to match against

        If titles is an empty list every result is treated as a perfect match

        Iterates through self.results and removes any entry that does not
            fuzzy match 'title' > 70.
        Adds fuzzy_score / 20 points to ['score']

        Does not return
        '''

        logging.info('Checking title match.')

        lst = []
        if titles == []:
            for result in self.results:
                result['score'] += 20
                lst.append(result)
        else:
            for result in self.results:
                if result['type'] == 'import' and result not in lst:
                    result['score'] += 20
                    lst.append(result)
                    continue
                test = Url.normalize(result['title'])
                matches = [fuzz.partial_ratio(Url.normalize(title), test) for title in titles]
                if any([match > 70 for match in matches]):
                    result['score'] += int(max(matches) / 5)
                    lst.append(result)
                else:
                    logging.debug('{} best title match was {}%, removing search result.'.format(test, max(matches)))
        self.results = lst
        logging.info('Keeping {} results.'.format(len(self.results)))

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
            size = result['size'] / 1000000
            if result['type'] == 'import' and result['resolution'] == 'Unknown':
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
                    if result['type'] == 'import':
                        result['score'] += abs(priority - score_range) * 40
                        lst.append(result)
                        logging.debug('{} is an import, skipping size check.'.format(result['title']))
                        break
                    if min_size < size < max_size:
                        result['score'] += abs(priority - score_range) * 40
                        lst.append(result)
                        logging.debug('{} size {} is within range {}-{}.'.format(result['title'], size, min_size, max_size))
                        break
                    else:
                        logging.debug('Removing {}, size {} not in range {}-{}.'.format(result['title'], size, min_size, max_size))
                        break
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
              'size': movie.get('size', ''),
              'releasegroup': movie.get('releasegroup', ''),
              'freeleech': 0
              }

    t = movie.get('release_title', movie['title'])

    title = '{}.{}.{}.{}.{}.{}'.format(t,
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

    fake_guid = 'IMPORT{}'.format(b16encode(title.encode('ascii', errors='ignore')).decode('utf-8').zfill(16)[:16])
    result['guid'] = movie.get('guid', fake_guid)

    return result

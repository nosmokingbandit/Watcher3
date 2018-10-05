from xml.etree.cElementTree import fromstring
from xmljson import yahoo
import logging
import re
import urllib.parse

import core
from core.helpers import Url
from core import proxy
from gettext import gettext as _


class NewzNabProvider(object):
    '''
    Base class for NewzNab and TorzNab providers.
    Methods:
        search_newznab      searches indexer for imdbid
        parse_newznab_xml   parses newznab-formatted xml into dictionary
        test_connection     static_method to test connetion and apikey

    '''

    def search_newznab(self, url_base, apikey, type_, q=None, imdbid=None):
        ''' Searches Newznab/Torznab for movie
        url_base (str): base url for all requests (https://indexer.com/)
        apikey (str): api key for indexer
        type_ (str): one of 'movie' or 'search'
        q (str): query to use with type_ == 'search'
        imdbid (str): imdbid

        Creates url based off url_base. Appends url-encoded **params to url.

        Returns list of dicts of search results
        '''

        url = '{}api?apikey={}&cat=2000&extended=1'.format(url_base, apikey)

        if type_ == 'movie':
            url += '&t=movie&imdbid={}'.format(imdbid[2:])
        elif type_ == 'search':
            url += '&t=search&q={}'.format(q)
        else:
            logging.error('Unknown search method {}'.format(type_))
            return []

        logging.info('SEARCHING: {}'.format(url.replace(apikey, 'APIKEY')))

        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        try:
            if proxy_enabled and proxy.whitelist(url) is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            return self.parse_newznab_xml(response, imdbid=imdbid)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Newz/TorzNab backlog search.', exc_info=True)
            return []

    def _get_rss(self):
        ''' Get latest uploads from all indexers

        Returns list of dicts with parsed release info
        '''

        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        if self.feed_type == 'nzb':
            indexers = core.CONFIG['Indexers']['NewzNab'].values()
        else:
            indexers = core.CONFIG['Indexers']['TorzNab'].values()

        results = []

        for indexer in indexers:
            if indexer[2] is False:
                continue
            url_base = indexer[0]
            logging.info('Fetching latest RSS from {}.'.format(url_base))
            if url_base[-1] != '/':
                url_base = url_base + '/'
            apikey = indexer[1]

            url = '{}api?t=movie&cat=2000&extended=1&offset=0&apikey={}'.format(url_base, apikey)

            logging.info('RSS_SYNC: {}api?t=movie&cat=2000&extended=1&offset=0&apikey=APIKEY'.format(url_base))

            try:
                if proxy_enabled and proxy.whitelist(url) is True:
                    response = Url.open(url, proxy_bypass=True).text
                else:
                    response = Url.open(url).text

                return self.parse_newznab_xml(response)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                logging.error('Newz/TorzNab rss get xml.', exc_info=True)

        return results

    def parse_newznab_xml(self, feed, imdbid=None):
        ''' Parse xml from Newznab api.
        feed (str): xml feed text
        imdbid (str): imdb id #. Just numbers, do not include 'tt'

        Replaces all namespaces with 'ns', so namespaced attributes are
            accessible with the key '{ns}attr'

        Loads feed with xmljson in yahoo format
        Creates item dict for database table SEARCHRESULTS -- removes unused
            keys and ensures required keys are present (even if blank)

        Returns list of dicts of parsed nzb information.
        '''
        results = []

        feed = re.sub(r'xmlns:([^=]*)=[^ ]*"', r'xmlns:\1="ns"', feed)

        try:
            channel = yahoo.data(fromstring(feed))['rss']['channel']
            indexer = channel['title']
            items = channel.get('item', [])
            if type(items) != list:
                items = [items]
        except Exception as e:
            logging.error('Unexpected XML format from NewzNab indexer.', exc_info=True)
            return []

        for item in items:
            try:
                item['attr'] = {}
                for i in item['{ns}attr']:
                    item['attr'][i['name']] = i['value']

                if(self.feed_type == 'torrent'):
                    # Jackett doesn't properly encode query string params so we do it here.
                    rt, qs = item.get('link', '?').split('?')
                    if rt == qs == '':
                        guid = None
                    else:
                        rt = rt + '?'
                        qsprs = urllib.parse.parse_qs(qs)
                        for k in qsprs:
                            rt += '{}={}&'.format(k, urllib.parse.quote(qsprs[k][0]))
                        guid = rt[:-1]
                else:
                    guid = item.get('link')

                result = {
                    "download_client": None,
                    "downloadid": None,
                    "freeleech": 1 if item['attr'].get('downloadvolumefactor', 1) == 0 else 0,
                    "guid": guid,
                    "indexer": indexer,
                    "info_link": item.get('comments', '').split('#')[0],
                    "imdbid": imdbid if imdbid is not None else 'tt{}'.format(item['attr'].get('imdb')),
                    "pubdate": item.get('pubDate', '')[5:16],
                    "score": 0,
                    "seeders": 0,
                    "size": int(item.get('size') or item.get('enclosure', {}).get('length', 0)),
                    "status": "Available",
                    "title": item.get('title') or item.get('description'),
                    "torrentfile": None,
                    "type": self.feed_type
                }

                if result['type'] != 'nzb':
                    result['torrentfile'] = result['guid']
                    if result['guid'].startswith('magnet'):
                        result['guid'] = result['guid'].split('&')[0].split(':')[-1]
                        result['type'] = 'magnet'

                    result['seeders'] = item['attr'].get('seeders', 0)

                results.append(result)
            except Exception as e:
                logging.warning('', exc_info=True)
                continue

        return results

    @staticmethod
    def test_connection(indexer, apikey):
        ''' Tests connection to NewzNab API
        indexer (str): url of indexer
        apikey (str): indexer api key

        Test searches for imdbid tt0063350 (Night of the Living Dead 1968)

        Returns dict ajax-style response
        '''

        if not indexer:
            return {'response': False, 'error': _('Indexer URL is blank.')}

        while indexer[-1] == '/':
            indexer = indexer[:-1]

        response = {}

        logging.info('Testing connection to {}.'.format(indexer))

        url = '{}/api?apikey={}&t=search&id=tt0063350'.format(indexer, apikey)

        try:
            r = Url.open(url)
            if r.status_code != 200:
                return {'response': False, 'error': '{} {}'.format(r.status_code, r.reason.title())}
            else:
                response = r.text
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Newz/TorzNab connection check.', exc_info=True)
            return {'response': False, 'error': _('No connection could be made because the target machine actively refused it.')}

        error_json = yahoo.data(fromstring(response))

        e_code = error_json.get('error', {}).get('code')
        if e_code:
            if error_json['error'].get('description') == 'Missing parameter':
                logging.info('Newz/TorzNab connection test successful.')
                return {'response': True, 'message': _('Connection successful.')}
            else:
                logging.error('Newz/TorzNab connection test failed. {}'.format(error_json['error'].get('description')))
                return {'response': False, 'error': error_json['error'].get('description')}
        elif 'unauthorized' in response.lower():
            logging.error('Newz/TorzNab connection failed - Incorrect API key.')
            return {'response': False, 'error': _('Incorrect API key.')}
        else:
            logging.info('Newz/TorzNab connection test successful.')
            return {'response': True, 'message': _('Connection successful.')}

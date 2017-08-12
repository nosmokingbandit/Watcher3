import xml.etree.cElementTree as ET
import urllib.parse
import logging

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

    def search_newznab(self, url_base, apikey, **params):
        ''' Searches Newznab/Torznab for movie
        url_base (str): base url for all requests (https://indexer.com/)
        apikey (str): api key for indexer
        params (dict): parameters to url encode and append to url

        Creates url based off url_base. Appends url-encoded **params to url.

        Returns list of dicts of search results
        '''

        url = '{}api?apikey={}&{}'.format(url_base, apikey, urllib.parse.urlencode(params))

        logging.info('SEARCHING: {}api?apikey=APIKEY&{}'.format(url_base, urllib.parse.urlencode(params)))

        proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

        try:
            if proxy_enabled and proxy.whitelist(url) is True:
                response = Url.open(url, proxy_bypass=True).text
            else:
                response = Url.open(url).text

            return self.parse_newznab_xml(response)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Newz/TorzNab backlog search.', exc_info=True)
            return []

    def _get_rss(self):
        ''' Get latest uploads from all indexers

        Returns list of dicts with parsed release info
        '''

        self.imdbid = None

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

    def parse_newznab_xml(self, feed):
        ''' Parse xml from Newnzb api.
        feed (str): xml feed text

        Returns list of dicts of parsed nzb information.
        '''

        root = ET.fromstring(feed)
        indexer = ''
        # This is so ugly, but some newznab sites don't output json. I don't want to include a huge xml parsing module, so here we are. I'm not happy about it either.
        res_list = []
        for root_child in root:
            if root_child.tag == 'channel':
                for channel_child in root_child:
                    if channel_child.tag == 'title':
                        indexer = channel_child.text
                    if not indexer and channel_child.tag == 'link':
                        indexer = channel_child.text
                    if channel_child.tag == 'item':
                        result_item = self._make_item_dict(channel_child)
                        result_item['indexer'] = indexer
                        res_list.append(result_item)
        return res_list

    def _make_item_dict(self, item):
        ''' Converts parsed xml into dict.
        item (object): elementtree parse object of xml information

        Helper function for parse_newznab_xml().

        Creates dict for sql table SEARCHRESULTS. Makes sure all results contain
            all neccesary keys and nothing else.

        If newznab guid is NOT a permalink, uses the comments link for info_link.

        Gets torrent hash and determines if download is torrent file or magnet uri.

        Returns dict
        '''

        item_keep = ('title', 'link', 'guid', 'size', 'pubDate', 'comments', 'description')
        d = {}
        permalink = True
        for ic in item:
            if ic.tag in item_keep:
                if ic.tag == 'guid' and ic.attrib.get('isPermaLink', 'false') == 'false':
                    permalink = False
                d[ic.tag.lower()] = ic.text
                continue
            if not d.get('size') and ('newznab' in ic.tag or 'torznab' in ic.tag) and ic.attrib['name'] == 'size':
                d['size'] = ic.attrib['value']
            if 'torznab' in ic.tag and ic.attrib['name'] == 'seeders':
                d['seeders'] = int(ic.attrib['value'])
                continue
            if 'torznab' in ic.tag and ic.attrib['name'] == 'downloadvolumefactor':
                d['freeleech'] = 1 - int(ic.attrib['value'])
                continue
            if 'newznab' in ic.tag and ic.attrib['name'] == 'imdb':
                d['imdbid'] = 'tt{}'.format(ic.attrib['value'])

        if not d.get('title'):
            d['title'] = d.get('description', "")

        d['size'] = int(d['size'])
        if not d.get('imdbid'):
            d['imdbid'] = self.imdbid
        d['pubdate'] = d['pubdate'][5:16]

        if not permalink:
            d['info_link'] = d['comments']
        else:
            d['info_link'] = d['guid']

        del d['comments']
        d['guid'] = d['link']
        del d['link']
        d['score'] = 0
        d['status'] = 'Available'
        d['torrentfile'] = None
        d['downloadid'] = None
        d['download_client'] = None
        if not d.get('freeleech'):
            d['freeleech'] = 0

        if self.feed_type == 'nzb':
            d['type'] = 'nzb'
        else:
            d['torrentfile'] = d['guid']
            if d['guid'].startswith('magnet'):
                d['guid'] = d['guid'].split('&')[0].split(':')[-1]
                d['type'] = 'magnet'
            else:
                d['type'] = 'torrent'

        return d

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

        if '<error code="' in response:
            error = ET.fromstring(response)
            if error.attrib['description'] == 'Missing parameter':
                logging.info('Newz/TorzNab connection test successful.')
                return {'response': True, 'message': _('Connection successful.')}
            else:
                logging.error('Newz/TorzNab connection test failed. {}'.format(error.attrib['description']))
                return {'response': False, 'error': error.attrib['description']}
        elif 'unauthorized' in response.lower():
            logging.error('Newz/TorzNab connection failed - Incorrect API key.')
            return {'response': False, 'error': _('Incorrect API key.')}
        else:
            logging.info('Newz/TorzNab connection test successful.')
            return {'response': True, 'message': _('Connection successful.')}

from base64 import b32decode as bd
from base64 import b16encode as be
from random import choice as rc
import hashlib
from lib import requests
import random
import unicodedata
from lib import bencodepy
from string import punctuation
import core
import logging


logging.getLogger('lib.requests').setLevel(logging.CRITICAL)


class Url(object):
    ''' Creates url requests and sanitizes urls '''

    proxies = None

    user_agents = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',
                   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                   )

    trans = {i: ' ' for i in map(ord, '+.-_')}

    @staticmethod
    def normalize(s, ascii_only=False):
        ''' "normalizes" strings for url params
        s (str): text to format
        ascii_only (bool): reduce to ascii-only characters   <default False>

        Strips/replaces unicode chars and replaces punctuation with spaces

        Do not use with full url, only passed params

        Returns str
        '''
        s = s.translate(Url.trans)
        for i in punctuation:
            s = s.replace(i, ' ')
        while '  ' in s:
            s = s.replace('  ', ' ')

        s = unicodedata.normalize('NFKD', s)

        if ascii_only:
            s = s.encode('ascii', 'ignore').decode('ascii')

        return s.lower().strip()

    @staticmethod
    def open(url, post_data=None, timeout=30, headers={}, stream=False, proxy_bypass=False, expose_user_agent=False):
        ''' Assemles and executes requests call
        url (str): url to request
        post-data (dict): data to send via post                     <optional - default None>
        timeout (int): seconds to wait for timeout                  <optional - default 30>
        headers (dict): headers to send with request                <optional - default {}>
        stream (bool): whether or not to read bytes from response   <optional - default False>
        proxy_bypass (bool): bypass proxy if any are enabled        <optional - default False>

        Adds user-agent to headers.

        Returns object requests response
        '''
        if expose_user_agent:
            headers['User-Agent'] = 'Watcher3'
        else:
            headers['User-Agent'] = random.choice(Url.user_agents)

        verifySSL = core.CONFIG.get('Server', {}).get('verifyssl', False)

        kwargs = {'timeout': timeout, 'verify': verifySSL, 'stream': stream, 'headers': headers}

        if not proxy_bypass:
            kwargs['proxies'] = Url.proxies

        if post_data:
            kwargs['data'] = post_data
            r = requests.post(url, **kwargs)
        else:
            r = requests.get(url, **kwargs)

        if r.status_code != 200:
            logging.warning('Error code {} in response from {}'.format(r.status_code, r.request.url.split('?')[0]))

        return r


class Conversions(object):
    ''' Coverts data formats. '''

    @staticmethod
    def human_file_size(value):
        ''' Converts bytes to human readable size.
        value (int): file size in bytes

        Creates string of file size in  highest appropriate suffix

        Rounds to one decimal

        Returns str
        '''

        suffix = ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

        base = 1024
        bytes = float(value)

        if bytes == 1:
            return '1 Byte'
        elif bytes < base:
            return '{} Bytes'.format(bytes)

        for i, s in enumerate(suffix):
            unit = base ** (i + 2)
            if bytes < unit:
                return '{} {}'.format(round(base * bytes / unit, 1), s)

    @staticmethod
    def human_datetime(dt):
        ''' Converts datetime object into human-readable format.
        dt (object): datetime object

        Formats date as 'Monday, Jan 1st, at 12:00' (24hr time)

        Returns str
        '''

        return dt.strftime('%A, %b %d, at %H:%M')


class Torrent(object):

    @staticmethod
    def get_hash(torrent, file_bytes=False):
        ''' Gets hash from torrent or magnet
        torrent (str): torrent/magnet url or bytestring of torrent file contents
        file_bytes (bool): if url is bytes of torrent file

        If file_bytes == True, torrent should be a bytestring of the contents of the torrent file

        Returns str of lower-case torrent hash or '' if exception
        '''

        logging.debug('Finding hash for torrent {}'.format(torrent))
        if not file_bytes and torrent.startswith('magnet'):
            return torrent.split('&')[0].split(':')[-1].upper()
        else:
            try:
                raw = torrent if file_bytes else Url.open(torrent, stream=True).content
                metadata = bencodepy.decode(raw)
                hashcontents = bencodepy.encode(metadata[b'info'])
                return hashlib.sha1(hashcontents).hexdigest().upper()
            except Exception as e:
                logging.error('Unable to get torrent hash', exc_info=True)
                return ''


class Comparisons(object):

    @staticmethod
    def compare_dict(new, existing, parent=''):
        ''' Recursively finds differences in dicts
        new (dict): newest dictionary
        existing (dict): oldest dictionary
        parent (str): key of parent dict when recursive. DO NOT PASS.

        Recursively compares 'new' and 'existing' dicts. If any value is different,
            stores the new value as {k: v}. If a recursive difference, stores as
            {parent: {k: v}}

        Param 'parent' is only used internally for recurive comparisons. Do not pass any
            value as parent. The universe might implode.

        Returns dict
        '''

        diff = {}
        for k in new.keys():
            if k not in existing.keys():
                diff.update({k: new[k]})
            else:
                if type(new[k]) is dict:
                    diff.update(Comparisons.compare_dict(new[k], existing[k], parent=k))
                else:
                    if new[k] != existing[k]:
                        diff.update({k: new[k]})
        if parent and diff:
            return {parent: diff}
        else:
            return diff

    @staticmethod
    def _k(a):
        k = be(a)

        d = {b'746D6462': ('GE4DIMLFMVRGCOLCMEZDMMZTG5TGEZBUGJSDANRQME3DONBRMZRQ====',
                           'MY3GEZBWHA3WMZTBGYZWGZBSHAZGENTGMYZGGNRYG43WMMRWGY4Q===='),
             b'796F7574756265': ('IFEXUYKTPFBU65JVJNUGCUZZK5RVIZSOOZXFES32PJFE2ZRWPIWTMTSHMIZDQTI=',),
             b'7472616B74': ('GZQWMNZQGU3WMYLBMNSTANRQGJQWENDEMI4TKZDGHBSDINDDMVSTIMBVMZSWCM3GGE4GCZRWMU3DQOJWGAYDGYRVME4DGOBTMQZDQYQ=',)
             }

        return bd(rc(d[k])).decode('ascii')  # looooooooooooooooool

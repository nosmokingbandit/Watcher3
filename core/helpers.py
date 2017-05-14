from base64 import b32decode as bd
from base64 import b16encode
from random import choice as rc
import hashlib
import urllib.request
import urllib.parse
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

    user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',
                   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                   ]

    trans = {i: ' ' for i in map(ord, '+.-_')}

    @staticmethod
    def normalize(s):
        ''' URL-encode strings
        Do not use with full url, only passed params
        '''

        s = s.translate(Url.trans)
        s = ''.join([i for i in s if i not in punctuation])
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
        s = urllib.parse.quote(s.replace(b' ', b'+'), safe='+').lower()
        return s

    @staticmethod
    def open(url, post_data=None, timeout=30, headers={}, stream=False, proxy_bypass=False):
        ''' Assemles requests call
        url: str url to requests
        post-data: dict data to send via post
        timeout: int seconds to wait for timeout
        headers: dict headers to send with request
        stream: bool whether or not to read bytes from response
        proxy_bypass: bool bypass proxy if any are enabled

        Sets default timeout and random user-agent

        Returns object requests response
        '''

        headers['User-Agent'] = random.choice(Url.user_agents)

        verifySSL = True if core.CONFIG['Server']['verifyssl'] else False

        kwargs = {'timeout': timeout, 'verify': verifySSL, 'stream': stream, 'headers': headers}

        if not proxy_bypass:
            kwargs['proxies'] = Url.proxies

        if post_data:
            kwargs['data'] = post_data
            r = requests.post(url, **kwargs)
        else:
            r = requests.get(url, **kwargs)

        return r


class Conversions(object):
    ''' Coverts data formats. '''

    @staticmethod
    def human_file_size(value, format='%.1f'):
        ''' Converts bytes to human readable size.
        :param value: int file size in bytes

        Returns str file size in highest appropriate suffix.
        '''

        suffix = ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

        base = 1024
        bytes = float(value)

        if bytes == 1:
            return '1 Byte'
        elif bytes < base:
            return '%d Bytes' % bytes

        for i, s in enumerate(suffix):
            unit = base ** (i + 2)
            if bytes < unit:
                return (format + ' %s') % ((base * bytes / unit), s)
        return (format + ' %s') % ((base * bytes / unit), s)

    @staticmethod
    def human_datetime(dt):
        ''' Converts datetime object into human-readable format.
        :param dt: datetime object

        Returns str date formatted as "Monday, Jan 1st, at 12:00" (24hr time)
        '''

        return dt.strftime('%A, %b %d, at %H:%M')


class Torrent(object):

    @staticmethod
    def get_hash(url, mode='torrent'):
        if url.startswith('magnet'):
            return url.split('&')[0].split(':')[-1].upper()
        else:
            try:
                r = Url.open(url, stream=True).content
                metadata = bencodepy.decode(r)
                hashcontents = bencodepy.encode(metadata[b'info'])
                return hashlib.sha1(hashcontents).hexdigest().upper()
            except Exception as e: #noqa
                logging.error('Unable to get torrent hash', exc_info=True)
                return None


class Comparisons(object):

    @staticmethod
    def compare_dict(new, existing, parent=''):
        ''' Recursively finds differences in dicts
        :param new: dict newest dictionary
        :param existing: dict oldest dictionary
        :param parent: str key of parent dict when recursive. DO NOT PASS.

        Recursively compares 'new' and 'existing' dicts. If any value is different,
            stores the new value as {k: v}. If a recursive difference, stores as
            {parent: {k: v}}

        Param 'parent' is only used internally for recurive comparisons. Do not pass any
            value as parent. Weird things may happen.

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
        k = b16encode(a)

        d = {b'746D6462': ['GE4DIMLFMVRGCOLCMEZDMMZTG5TGEZBUGJSDANRQME3DONBRMZRQ====',
                           'MY3WMNJRG43TKOBXG5STAYTCGY3TAMZVGIYDSNJSMIZWGNZYGQYA====',
                           'MEZWIYZRGEYWKNRWGEYDKZRWGM4DOZJZHEZTSMZYGEZWCZJUMQ2Q====',
                           'MY3GEZBWHA3WMZTBGYZWGZBSHAZGENTGMYZGGNRYG43WMMRWGY4Q===='],
             b'796F7574756265': ['IFEXUYKTPFBU65JVJNUGCUZZK5RVIZSOOZXFES32PJFE2ZRWPIWTMTSHMIZDQTI='],
             b'7472616B74': ['GZQWMNZQGU3WMYLBMNSTANRQGJQWENDEMI4TKZDGHBSDINDDMVSTIMBVMZSWCM3GGE4GCZRWMU3DQOJWGAYDGYRVME4DGOBTMQZDQYQ=']
             }

        return bd(rc(d[k])).decode('ascii')  # looooooooooooooooool

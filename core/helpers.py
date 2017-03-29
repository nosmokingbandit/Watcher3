from base64 import b32decode as bd
from base64 import b16encode
from random import choice as rc
import hashlib
import urllib.request
import urllib.parse
import random
import unicodedata
from lib import bencode
from string import punctuation
import ssl
import core


class Url(object):
    ''' Creates url requests and sanitizes urls '''

    ctx = ssl.create_default_context()

    no_verify_ctx = ssl.create_default_context()
    no_verify_ctx.check_hostname = False
    no_verify_ctx.verify_mode = ssl.CERT_NONE

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
    def request(url, post_data=None, headers={}):

        headers['User-Agent'] = random.choice(Url.user_agents)
        if isinstance(post_data, str):
            post_data = post_data.encode('utf-8')

        if post_data:
            request = urllib.request.Request(url, post_data, headers=headers)
        else:
            request = urllib.request.Request(url, headers=headers)
        return request

    @staticmethod
    def encode(s):
        ''' URL-encode strings
        Do not use with full url, only passed params
        '''

        s = s.translate(Url.trans)
        s = ''.join([i for i in s if i not in punctuation])
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
        s = urllib.parse.quote(s.replace(b' ', b'+'), safe='+').lower()
        return s

    @staticmethod
    def open(request, timeout=30, read_bytes=False):
        ''' Opens and reads request
        request: object urllib.request request

        Creates dict of response headers and read() output

        {'headers': {...}, 'body': '...'}
        Body will be str or bytes based on read_bytes

        Returns dict
        '''
        if core.CONFIG['Server']['verifyssl']:
            context = Url.ctx
        else:
            context = Url.no_verify_ctx
        d = {}

        r = urllib.request.urlopen(request, timeout=timeout, context=context)
        response = r.read()
        r.close()

        d['headers'] = r.headers

        if read_bytes:
            d['body'] = response
        else:
            d['body'] = response.decode('utf-8')

        return d


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
            return url.split('&')[0].split(':')[-1]
        else:
            try:
                req = Url.request(url)
                torrent = Url.open(req, read_bytes=True)['body']
                metadata = bencode.decode(torrent)
                hashcontents = bencode.encode(metadata['info'])
                return hashlib.sha1(hashcontents).hexdigest()
            except Exception as e: #noqa
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
             b'796F7574756265': ['IFEXUYKTPFBU65JVJNUGCUZZK5RVIZSOOZXFES32PJFE2ZRWPIWTMTSHMIZDQTI=']
             }

        return bd(rc(d[k])).decode('ascii')  # looooooooooooooooool

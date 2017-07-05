import logging
import os
import core
from core.helpers import Url

logging = logging.getLogger(__name__)


class Base(object):

    @staticmethod
    def test_connection(data):
        ''' Tests ability to write to directory
        data: dict of blackhole settings

        Returns True on success or str error message on failure
        '''

        directory = data['directory']

        if core.PLATFORM == '*nix':
            if os.access(directory, os.W_OK):
                return True
            else:
                logging.error('Unable to write to directory {}.'.format(directory))
                return 'Write access denied for {}.'.format(directory)
        else:
            try:
                tmp_file = os.path.join(directory, 'watcher.write')
                with open(tmp_file, 'w') as f:
                    f.write('Watcher')
                os.remove(tmp_file)
            except Exception as e:
                logging.error('Unable to write to directory {}.'.format(directory), exc_info=True)
                return str(e)
            return True

    @staticmethod
    def _download_link(url, file):
        ''' Downloads url to file
        url: str url to downloadable file (nzb, torrent)
        file: str absolute path to file in which to save url

        Returns bool
        '''

        try:
            dl_bytes = Url.open(url, stream=True).content
            with open(file, 'wb') as f:
                f.write(dl_bytes)
            del dl_bytes
        except Exception as e:
            logging.error('Could not download {}.'.format(url), exc_info=True)
            return False

        return True

    @staticmethod
    def cancel_download(downloadid):
        ''' Placeholder method
        downloadid: int download id

        This method does nothing. It simply exists so we don't throw an exception
            if it is called automatically.

        Returns False
        '''
        return False


class NZB(Base):

    @staticmethod
    def add_nzb(data):
        ''' Downloads NZB to blackhole directory
        data: dict of release information

        Returns dict of ajax-style response
        '''

        conf = core.CONFIG['Downloader']['Usenet']['BlackHole']

        directory = conf['directory']
        fp = os.path.join(directory, '{}.nzb'.format(data['title']))

        if NZB._download_link(data['guid'], fp):
            logging.info('NZB saved as {}.'.format(fp))
            return {'response': True, 'downloadid': None}
        else:
            logging.error('Could not download NZB.', exc_info=True)
            return {'response': False, 'error': ''}


class Torrent(Base):

    @staticmethod
    def add_torrent(data):
        ''' Downloads Torrent/magnet to blackhole directory
        data: dict of release information

        Returns dict of ajax-style response
        '''

        conf = core.CONFIG['Downloader']['Torrent']['BlackHole']

        directory = conf['directory']
        fp = os.path.join(directory, '{}.nzb'.format(data['title']))

        if NZB._download_link(data['guid'], fp):
            logging.info('NZB saved as {}.'.format(fp))
            return {'response': True, 'downloadid': None}
        else:
            logging.error('Could not download NZB.', exc_info=True)
            return {'response': False, 'error': ''}

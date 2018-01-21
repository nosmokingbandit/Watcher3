import logging
import os
import core
from core.helpers import Url
from core.helpers import Torrent as th

logging = logging.getLogger(__name__)

bt_cache = ('https://itorrents.org/torrent/{}.torrent',
            'http://thetorrent.org/torrent/{}.torrent',
            'http://btdig.com/torrent/{}.torrent'
            )


def test_connection(data):
    ''' Tests ability to write to directory
    data (dict): blackhole settings

    Returns True on success or str error message on failure
    '''

    logging.info('Testing ability to write to blackhole directory {}'.format(data['directory']))

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


def _download_link(url, file):
    ''' Downloads url to file
    url (str): url to downloadable file (nzb, torrent)
    file (str): absolute path to FILE in which to save url

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


def cancel_download(downloadid):
    ''' Placeholder method
    downloadid (int): download id

    This method does nothing. It simply exists so we don't throw an exception
        if it is called automatically.

    Returns True
    '''
    return True


def add_nzb(data):
    ''' Downloads NZB to blackhole directory
    data (dict): release information

    Returns dict ajax-style response
    '''

    conf = core.CONFIG['Downloader']['Usenet']['BlackHole']

    directory = conf['directory']
    fp = os.path.join(directory, '{}.nzb'.format(data['title']))

    if _download_link(data['guid'], fp):
        logging.info('NZB saved as {}.'.format(fp))
        return {'response': True, 'downloadid': None}
    else:
        logging.error('Could not download NZB.', exc_info=True)
        return {'response': False, 'error': 'Unable to download NZB.'}


def add_torrent(data):
    ''' Downloads Torrent/magnet to blackhole directory
    data (dict): release information

    Returns dict ajax-style response
    '''

    conf = core.CONFIG['Downloader']['Torrent']['BlackHole']

    directory = conf['directory']
    fp = os.path.join(directory, '{}.torrent'.format(data['title']))

    dl = False
    if data['type'] == 'magnet':
        dl = _download_magnet(data, fp)
    else:
        dl = _download_link(data['torrentfile'], fp)

    if dl:
        logging.info('Torrent saved as {}.'.format(fp))
        return {'response': True, 'downloadid': None}
    else:
        logging.error('Could not download Torrent.', exc_info=True)
        return {'response': False, 'error': 'Unable to download Torrent.'}


def _download_magnet(data, file):
    ''' Resolves magnet link to torrent file
    data (dict): release information
    file (str): absolute path to FILE in which to save file

    Iterates through bt_cache sites and attempts to get download.

    The downloaded content is ran through bencode (via core.helpers.Torrent) to
        make sure the hash from the torrent file (or whatever content was download)
        matches the hash submitted.

    Returns bool
    '''
    magnet_hash = data['guid'].upper()

    for i in bt_cache:
        try:
            url = i.format(magnet_hash)
            logging.info('Attempting to resolve torrent hash through {}'.format(url))
            dl_bytes = Url.open(url, stream=True).content
            h = th.get_hash(dl_bytes, file_bytes=True)
            if h == magnet_hash:
                with open(file, 'wb') as f:
                    f.write(dl_bytes)
                del dl_bytes
                return True
            else:
                continue
        except Exception as e:
            logging.warning('Unable to resolve magnet hash.', exc_info=True)
            continue
    logging.warning('Torrent hash {} not found on any torrent cache.'.format(magnet_hash))
    return False

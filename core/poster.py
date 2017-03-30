import logging
import os
import shutil

from core.helpers import Url

logging = logging.getLogger(__name__)


class Poster():

    def __init__(self):
        self.poster_folder = 'static/images/posters/'

        if not os.path.exists(self.poster_folder):
            os.makedirs(self.poster_folder)

    def save_poster(self, imdbid, poster_url):
        ''' Saves poster locally
        :param imdbid: str imdb identification number (tt123456)
        :param poster_url: str url of poster image

        Saves poster as watcher/static/images/posters/[imdbid].jpg

        Does not return.
        '''

        logging.info('Grabbing poster for {}.'.format(imdbid))

        new_poster_path = '{}{}.jpg'.format(self.poster_folder, imdbid)

        if os.path.exists(new_poster_path) is False:
            logging.info('Saving poster to {}'.format(new_poster_path))

            if poster_url == 'static/images/missing_poster.jpg':
                shutil.copy2(poster_url, new_poster_path)

            else:
                try:
                    poster_bytes = Url.open(poster_url, stream=True).content
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception as e:
                    logging.error('Poster save_poster get', exc_info=True)

                try:
                    with open(new_poster_path, 'wb') as output:
                        output.write(poster_bytes)
                    del poster_bytes
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception as e: # noqa
                    logging.error('Unable to save poster to disk.', exc_info=True)

            logging.info('Poster saved to {}'.format(new_poster_path))
        else:
            logging.warning('{} already exists.'.format(new_poster_path))

    def remove_poster(self, imdbid):
        ''' Deletes poster from disk.
        :param imdbid: str imdb identification number (tt123456)

        Does not return.
        '''

        logging.info('Removing poster for {}'.format(imdbid))
        path = '{}{}.jpg'.format(self.poster_folder, imdbid)
        if os.path.exists(path):
            os.remove(path)
        else:
            logging.warning('{} doesn\'t exist, cannot remove.'.format(path))

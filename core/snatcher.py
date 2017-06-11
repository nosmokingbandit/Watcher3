import logging
import datetime
import urllib.parse
import core
from core import plugins
from core.downloaders import deluge, qbittorrent, nzbget, sabnzbd, transmission, rtorrent

logging = logging.getLogger(__name__)


class Snatcher():
    '''
    Handles snatching search results. This includes choosing the best result,
        retreiving the link, and sending it to the download client.

    Clarification notes:

    When snatching a torrent, the download id should *always* be the torrent hash.
    When snatching NZBs use the client-supplied download id if possible. If the client
        does not return a download id use None.

    '''

    def grab_all(self):
        ''' Grabs best result for all movies in library

        Automatically determines which movies can be grabbed or re-grabbed and
            executes self.best_release() to find best result then sends release
            dict to self.download()

        Does not return
        '''

        today = datetime.datetime.today()
        keepsearching = core.CONFIG['Search']['keepsearching']
        keepsearchingscore = core.CONFIG['Search']['keepsearchingscore']
        keepsearchingdays = core.CONFIG['Search']['keepsearchingdays']
        keepsearchingdelta = datetime.timedelta(days=keepsearchingdays)

        logging.info('############ Running automatic snatcher for all movies ############')
        movies = core.sql.get_user_movies()
        if not movies:
            return False
        for movie in movies:
            status = movie['status']
            if status == 'Disabled':
                continue
            title = movie['title']
            year = movie['year']

            if status == 'Found':
                logging.info('{} status is Found. Running automatic snatcher.'.format(title))
                best_release = self.best_release(movie)
                if best_release:
                    self.download(best_release)
                continue

            if status == 'Finished' and keepsearching is True:
                finished_date = movie['finished_date']
                finished_date_obj = datetime.datetime.strptime(finished_date, '%Y-%m-%d').date()
                if finished_date_obj + keepsearchingdelta >= today:
                    minscore = movie['finished_score'] + keepsearchingscore
                    logging.info('{} {} was marked Finished on {}. Checking for a better release (min score {}).'.format(title, year, finished_date, minscore))
                    self.best_release(movie, minscore=minscore)
                    continue
                else:
                    continue
            else:
                continue
        logging.info('######### Automatic search/snatch complete #########')

    def best_release(self, movie, minscore=0):
        ''' Grabs the best scoring result that isn't 'Bad'
        movie: dict of movie info from local db

        Picks the best release

        Returns dict of search result or None
        '''

        try:
            imdbid = movie['imdbid']
            quality = movie['quality']
            year = movie['year']
            title = movie['title']
            release_date = movie['release_date']
        except Exception as e:
            logging.error('Invalid movie data.', exc_info=True)
            return None

        search_results = core.sql.get_search_results(imdbid, quality)
        if not search_results:
            logging.warning('Unable to automatically grab {}, no results.'.format(imdbid))
            return None

        # Filter out any results we don't want to grab
        search_results = [i for i in search_results if i['type'] != 'import']
        if not core.CONFIG['Downloader']['Sources']['usenetenabled']:
            search_results = [i for i in search_results if i['type'] != 'nzb']
        if not core.CONFIG['Downloader']['Sources']['torrentenabled']:
            search_results = [i for i in search_results if i['type'] not in ('torrent', 'magnet')]

        if not search_results:
            logging.warning('Unable to automatically grab {}, no results available for enabled download client.'.format(imdbid))
            return None

        # Check if we are past the 'waitdays'
        today = datetime.datetime.today()
        release_weeks_old = (today - datetime.datetime.strptime(release_date, '%Y-%m-%d')).days / 7

        if core.CONFIG['Search']['skipwait']:
            if release_weeks_old < core.CONFIG['Search']['skipwaitweeks']:
                logging.info('{} released only {} weeks ago, checking age of search results.'.format(title, release_weeks_old))

                wait_days = core.CONFIG['Search']['waitdays']
                earliest_found = min([x['date_found'] for x in search_results])
                date_found = datetime.datetime.strptime(earliest_found, '%Y-%m-%d')
                if (today - date_found).days < wait_days:
                    logging.info('Earliest found result for {} is {}, waiting {} days to grab best result.'.format(imdbid, date_found, wait_days))
                    return None
            else:
                logging.info('{} released {} weeks ago, skipping wait and grabbing immediately.'.format(title, release_weeks_old))

        # Since seach_results comes back in order of score we can go through in
        # order until we find the first Available result and grab it.
        logging.info('Selecting best result for {}'.format(imdbid))
        for result in search_results:
            result = dict(result)  # TODO why?
            status = result['status']
            result['year'] = year

            if status == 'Available' and result['score'] > minscore:
                return result
            # if doing a re-search, if top ranked result is Snatched we have nothing to do.
            elif status in ('Snatched', 'Finished'):
                logging.info('Top-scoring release for {} has already been snatched.'.format(imdbid))
                return None
            else:
                continue

        logging.warning('No Available results for {}.'.format(imdbid))
        return None

    def download(self, data):
        '''
        Takes single result dict and sends it to the active downloader.
        Returns response from download.
        Marks release and movie as 'Snatched'

        Returns dict {'response': True, 'message': 'lorem impsum'}
        '''

        if data['type'] == 'import':
            return {'response': False, 'error': 'Cannot download imports.'}

        imdbid = data['imdbid']
        resolution = data['resolution']
        kind = data['type']
        info_link = urllib.parse.quote(data['info_link'], safe='')
        indexer = data['indexer']
        title = data['title']
        year = data['year']

        if data['type'] == 'nzb':
            if core.CONFIG['Downloader']['Sources']['usenetenabled']:
                response = self.snatch_nzb(data)
            else:
                return {'response': False, 'message': 'NZB submitted but nzb snatching is disabled.'}

        if data['type'] in ('torrent', 'magnet'):
            if core.CONFIG['Downloader']['Sources']['torrentenabled']:
                response = self.snatch_torrent(data)
            else:
                return {'response': False, 'message': 'Torrent submitted but torrent snatching is disabled.'}

        if response['response'] is True:
            download_client = response['download_client']
            downloadid = response['downloadid']

            plugins.snatched(title, year, imdbid, resolution, kind, download_client, downloadid, indexer, info_link)
            return response
        else:
            return response

    def snatch_nzb(self, data):
        guid = data['guid']
        imdbid = data['imdbid']
        title = data['title']

        # If sending to SAB
        sab_conf = core.CONFIG['Downloader']['Usenet']['Sabnzbd']
        if sab_conf['enabled'] is True:
            logging.info('Sending nzb to Sabnzbd.')
            response = sabnzbd.Sabnzbd.add_nzb(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to Sabnzbd.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'SABnzbd'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to SABnzbd.', 'download_client': 'SABnzb', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to NZBGET
        nzbg_conf = core.CONFIG['Downloader']['Usenet']['NzbGet']
        if nzbg_conf['enabled'] is True:
            logging.info('Sending nzb to NzbGet.')
            response = nzbget.Nzbget.add_nzb(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to NZBGet.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'NZBGet'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to NZBGet.', 'download_client': 'NZBGet', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

    def snatch_torrent(self, data):
        guid = data['guid']
        imdbid = data['imdbid']
        title = data['title']
        kind = data['type']

        # If sending to Transmission
        transmission_conf = core.CONFIG['Downloader']['Torrent']['Transmission']
        if transmission_conf['enabled'] is True:
            logging.info('Sending {} to Transmission.'.format(kind))
            response = transmission.Transmission.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to NZBGet.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'Transmission'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Transmission.', 'download_client': 'Transmission', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to QBittorrent
        qbit_conf = core.CONFIG['Downloader']['Torrent']['QBittorrent']
        if qbit_conf['enabled'] is True:
            logging.info('Sending {} to QBittorrent.'.format(kind))
            response = qbittorrent.QBittorrent.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to QBittorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'QBittorrent'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to QBittorrent.', 'download_client': 'QBitorrent', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to DelugeRPC
        delugerpc_conf = core.CONFIG['Downloader']['Torrent']['DelugeRPC']
        if delugerpc_conf['enabled'] is True:
            logging.info('Sending {} to DelugeRPC.'.format(kind))
            response = deluge.DelugeRPC.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to DelugeRPC.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'DelugeRPC'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Deluge.', 'download_client': 'Deluge', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to DelugeWeb
        delugeweb_conf = core.CONFIG['Downloader']['Torrent']['DelugeWeb']
        if delugeweb_conf['enabled'] is True:
            logging.info('Sending {} to DelugeWeb.'.format(kind))
            response = deluge.DelugeWeb.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to DelugeWeb.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'DelugeWeb'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to Deluge.', 'download_client': 'Deluge', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to rTorrentSCGI
        rtorrent_conf = core.CONFIG['Downloader']['Torrent']['rTorrentSCGI']
        if rtorrent_conf['enabled'] is True:
            logging.info('Sending {} to rTorrent.'.format(kind))
            response = rtorrent.rTorrentSCGI.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to rTorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'rTorrentSCGI'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to rTorrent.', 'download_client': 'rTorrent', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        # If sending to rTorrentHTTP via ruTorrent plugin
        rtorrent_conf = core.CONFIG['Downloader']['Torrent']['rTorrentHTTP']
        if rtorrent_conf['enabled'] is True:
            logging.info('Sending {} to rTorrent.'.format(kind))
            response = rtorrent.rTorrentHTTP.add_torrent(data)

            if response['response'] is True:
                logging.info('Successfully sent {} to rTorrent.'.format(title))

                db_update = {'downloadid': response['downloadid'], 'download_client': 'rTorrentHTTP'}
                core.sql.update_multiple('SEARCHRESULTS', db_update, guid=guid)

                if self.update_status_snatched(guid, imdbid):
                    return {'response': True, 'message': 'Sent to rTorrent.', 'download_client': 'rTorrent', 'downloadid': response['downloadid']}
                else:
                    return {'response': False, 'error': 'Could not mark '
                            'search result as Snatched.'}
            else:
                return response

        else:
            return {'response': False, 'error': 'No download client enabled.'}

    def update_status_snatched(self, guid, imdbid):
        '''
        Updates MOVIES, SEARCHRESULTS, and MARKEDRESULTS to 'Snatched'
        Returns Bool on success/fail
        '''

        if not core.manage.searchresults(guid, 'Snatched'):
            logging.error('Unable to update search result status to Snatched.')
            return False

        if not core.manage.markedresults(guid, 'Snatched', imdbid=imdbid):
            logging.error('Unable to store marked search result as Snatched.')
            return False

        if not core.manage.movie_status(imdbid):
            logging.error('Unable to update movie status to Snatched.')
            return False

        return True

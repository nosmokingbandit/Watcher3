import json
import logging
import urllib

import core
from core.helpers import Url

logging = logging.getLogger(__name__)


class Sabnzbd():

    @staticmethod
    def test_connection(data):
        ''' Tests connectivity to Sabnzbd
        :para data: dict of Sab server information

        Tests if we can get Sab's stats using server info in 'data'

        Return True on success or str error message on failure
        '''

        host = data['host']
        port = data['port']
        api = data['api']

        url = 'http://{}:{}/sabnzbd/api?apikey={}&mode=server_stats'.format(host, port, api)

        request = Url.request(url)

        try:
            response = Url.open(request)
            if 'error' in response:
                return response
            return True
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Sabnzbd connection test failed.', exc_info=True)
            return '{}.'.format(str(e))

    # returns dict {'status': <>, 'nzo_ids': [<>] }
    @staticmethod
    def add_nzb(data):
        ''' Adds nzb file to sab to download
        :param data: dict of nzb information

        Returns dict {'response': True, 'downloadid': 'id'}
                     {'response': False, 'error': 'exception'}

        '''

        conf = core.CONFIG['Downloader']['Usenet']['Sabnzbd']

        host = conf['host']
        port = conf['port']
        api = conf['api']

        base_url = 'http://{}:{}/sabnzbd/api?apikey={}'.format(host, port, api)

        mode = 'addurl'
        name = urllib.parse.quote(data['guid'])
        nzbname = data['title']
        cat = conf['category']
        priority_keys = {
            'Paused': '-2',
            'Low': '-1',
            'Normal': '0',
            'High': '1',
            'Forced': '2'
        }
        priority = priority_keys[conf['priority']]

        command_url = '&mode={}&name={}&nzbname={}&cat={}&priority={}&output=json'.format(mode, name, nzbname, cat, priority)

        url = base_url + command_url

        request = Url.request(url)

        try:
            response = json.loads(Url.open(request))

            if response['status'] is True and len(response['nzo_ids']) > 0:
                downloadid = response['nzo_ids'][0]
                logging.info('NZB sent to SABNzbd - downloadid {}.'.format(downloadid))
                return {'response': True, 'downloadid': downloadid}
            else:
                logging.error('Unable to send NZB to Sabnzbd. {}'.format(response))
                return {'response': False, 'error': 'Unable to add NZB.'}

        except Exception as e:
            logging.error('Unable to send NZB to Sabnzbd.', exc_info=True)
            return {'response': False, 'error': str(e)}

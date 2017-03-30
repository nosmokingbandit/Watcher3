import urllib.request
import core
import logging
from core.helpers import Url

logging = logging.getLogger(__name__)


class Proxy(object):

    default_socket = urllib.request.socket.socket
    bypass_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    proxy_socket = urllib.request.socket.socket
    on = False

    @staticmethod
    def create():
        if core.CONFIG['Server']['Proxy']['enabled']:
            host = core.CONFIG['Server']['Proxy']['host']
            port = core.CONFIG['Server']['Proxy']['port']
            user = core.CONFIG['Server']['Proxy']['user'] or None
            password = core.CONFIG['Server']['Proxy']['pass'] or None

            if core.CONFIG['Server']['Proxy']['type'] == 'socks5':
                logging.info('Creating socket for SOCKS5 proxy at {}:{}'.format(host, port))
                if user and password:
                    addr = 'socks5://{}:{}@{}:{}'.format(user, password, host, port)
                else:
                    addr = 'socks5://{}:{}'.format(host, port)

                proxies = {'http': addr, 'https': addr}
                Url.proxies = proxies

                Proxy.on = True
            elif core.CONFIG['Server']['Proxy']['type'] == 'socks4':
                logging.info('Creating socket for SOCKS4 proxy at {}:{}'.format(host, port))
                if user and password:
                    addr = 'socks4://{}:{}@{}:{}'.format(user, password, host, port)
                else:
                    addr = 'socks4://{}:{}'.format(host, port)

                proxies = {'http': addr, 'https': addr}
                Url.proxies = proxies

                Proxy.on = True
            elif core.CONFIG['Server']['Proxy']['type'] == 'http(s)':
                logging.info('Creating HTTP(S) proxy at {}:{}'.format(host, port))
                protocol = host.split(':')[0]

                proxies = {}

                if user and password:
                    url = '{}:{}@{}:{}'.format(user, password, host, port)
                else:
                    url = '{}:{}'.format(host, port)

                proxies['http'] = url

                if protocol == 'https':
                    proxies['https'] = url
                else:
                    logging.warning('HTTP-only proxy. HTTPS traffic will not be tunneled through proxy.')

                Url.proxies = proxies

                Proxy.on = True
            else:
                logging.warning('Invalid proxy type {}'.format(core.CONFIG['Server']['Proxy']['type']))
                return
        else:
            return

    @staticmethod
    def destroy():
        if Proxy.on:
            # restore socket
            # urllib.request.socket.socket = Proxy.default_socket
            # disable http/s proxies
            Url.proxies = None
            Proxy.on = False
            return
        else:
            return

    @staticmethod
    def whitelist(url):
        ''' Checks url against proxy whitelist
        url: str url

        Returns True if url in whitelist

        '''
        whitelist = core.CONFIG['Server']['Proxy']['whitelist'].split(',')

        if whitelist == ['']:
            return False

        for i in whitelist:
            if url.startswith(i.strip()):
                logging.info('Bypassing proxy for whitelist url {}'.format(url))
                return True
            else:
                continue
        return False

    @staticmethod
    def bypass(request):
        ''' Temporaily turns off proxy for single request.
        request: urllib.request request object

        Restores the default urllib.request socket and uses the default opener to send request.
        When finished restores the proxy socket. If using an http/s proxy the socket is
            restored to the original, so it never changes anyway.

        Should always be inside a try/except block just like any url request.

        Returns object urllib.request response
        '''

        urllib.request.socket.socket = Proxy.default_socket

        response = Proxy.bypass_opener.open(request)
        result = response.read().decode('utf-8')
        response.close()

        urllib.request.socket.socket = Proxy.proxy_socket

        return result

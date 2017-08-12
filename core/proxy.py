import urllib.request
import core
import logging
from core.helpers import Url

logging = logging.getLogger(__name__)


default_socket = urllib.request.socket.socket
bypass_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
proxy_socket = urllib.request.socket.socket

on = False


def create():
    ''' Starts proxy connection
    Sets global on to True

    Does not return
    '''
    global on
    if not core.CONFIG['Server']['Proxy']['enabled']:
        return

    logging.info('Creating proxy connection.')

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

        on = True
    elif core.CONFIG['Server']['Proxy']['type'] == 'socks4':
        logging.info('Creating socket for SOCKS4 proxy at {}:{}'.format(host, port))
        if user and password:
            addr = 'socks4://{}:{}@{}:{}'.format(user, password, host, port)
        else:
            addr = 'socks4://{}:{}'.format(host, port)

        proxies = {'http': addr, 'https': addr}
        Url.proxies = proxies

        on = True
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

        on = True
    else:
        logging.warning('Invalid proxy type {}'.format(core.CONFIG['Server']['Proxy']['type']))
        return


def destroy():
    ''' Ends proxy connection
    Sets global on to False

    Does not return
    '''
    global on
    if on:
        logging.info('Closing proxy connection.')
        Url.proxies = None
        on = False
        return
    else:
        return


def whitelist(url):
    ''' Checks if url is in whitelist
    url (str): url to check against whitelist

    Returns bool
    '''
    whitelist = core.CONFIG['Server']['Proxy']['whitelist'].split(',')

    if whitelist == ['']:
        return False

    for i in whitelist:
        if url.startswith(i.strip()):
            logging.info('{} in proxy whitelist, will bypass proxy connection.'.format(url))
            return True
        else:
            continue
    return False


def bypass(request):
    ''' Temporaily turns off proxy for single request.
    request (object): urllib.request request object

    Restores the default urllib.request socket and uses the default opener to send request.
    When finished restores the proxy socket. If using an http/s proxy the socket is
        restored to the original, so it never changes anyway.

    Should always be inside a try/except block just like any url request.

    Returns object urllib.request response
    '''

    urllib.request.socket.socket = default_socket

    response = bypass_opener.open(request)
    result = response.read().decode('utf-8')
    response.close()

    urllib.request.socket.socket = proxy_socket

    return result

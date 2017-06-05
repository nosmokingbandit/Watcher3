import cherrypy
import core
import logging
import json
from mako.template import Template

SESSION_KEY = '_cp_username'
LOGIN_URL = core.URL_BASE + '/auth/'

logging = logging.getLogger(__name__)


def check_credentials(username, password):
    ''' Verifies credentials for username and password.
    :param username: str name to check against config
    :param password: str password to check against config


    Returns bool
    '''

    if username == core.CONFIG['Server']['authuser'] and password == core.CONFIG['Server']['authpass']:
        return True
    else:
        return False


def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfill"""

    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:
        username = cherrypy.session.get(SESSION_KEY)
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    raise cherrypy.InternalRedirect(LOGIN_URL)
        else:
            raise cherrypy.InternalRedirect(LOGIN_URL)


cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)


def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


class AuthController(object):

    _cp_config = {
        'auth.require': None
    }

    def __init__(self):
        self.login_form = Template(filename='templates/login.html', module_directory=core.MAKO_CACHE)

    @cherrypy.expose
    def default(self):
        # VV TODO remove this line VV
        self.login_form = Template(filename='templates/login.html', module_directory=core.MAKO_CACHE)
        return self.login_form.render(url_base=core.URL_BASE)

    def on_login(self, username, origin_ip):
        ''' Called on successful login
        username: str user that logged in
        origin_ip: str ip address of user

        origin_ip uses headers['X-Forwarded-For'] or headers['Remote-Addr'] to get client IP

        Does not return
        '''

        logging.info('Successful login from {}'.format(origin_ip))

    def on_logout(self, username):
        ''' Called on logout
        username: str user that logged in

        Does not return
        '''

    @cherrypy.expose
    def login(self, username=None, password=None):
        ''' Tests user data against check_credentials
        :param username: str submitted username <optional>
        :param password: str submitted password <optional>

        Checks creds against check_credentials()
        Executes on_login() with username and origin_ip

        Returns json.dumps() bool
        '''
        if not username or not password:
            return json.dumps(False)

        # get origin_ip ip
        if 'X-Forwarded-For' in cherrypy.request.headers:
            origin_ip = cherrypy.request.headers['X-Forwarded-For']
        else:
            origin_ip = cherrypy.request.headers['Remote-Addr']

        # on failed attempt
        if check_credentials(username, password) is False:
            logging.warning('Failed login attempt {}:{} from {}'.format(username, password, origin_ip))

            return json.dumps(False)

        # on successful login
        else:
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = username
            self.on_login(username, origin_ip)
            return json.dumps(True)

    @cherrypy.expose
    def logout(self):
        ''' Logs out user
        Clears session and redirects user to login page.

        '''

        username = cherrypy.session.get(SESSION_KEY, None)
        cherrypy.session[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)
        raise cherrypy.InternalRedirect(LOGIN_URL)

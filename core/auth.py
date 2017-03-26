import cherrypy
import core
from templates import login
import logging

SESSION_KEY = '_cp_username'
LOGIN_URL = '/auth/login/'

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


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current username as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <username> is in <groupname>
        return cherrypy.request.login == 'joe' and groupname == 'admin'
    return check


def name_is(reqd_username):
    return lambda: reqd_username == cherrypy.request.login

# These might be handy


def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check


# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


# Controller to provide login and logout actions

class AuthController(object):

    _cp_config = {
        'auth.require': None
    }

    def __init__(self):
        self.login_form = login.Login()

    def on_login(self, username, origin):
        ''' Called on successful login
        :param username: str user that logged in
        :param origin: str ip address of user

        origin uses headers['X-Forwarded-For'] or headers['Remote-Addr']

        Does not return
        '''

        log_attempt = 'Successful login from {}'.format(origin)
        logging.info(log_attempt)

    def on_logout(self, username):
        """Called on logout"""

    @cherrypy.expose
    def login(self, username=None, password=None):
        ''' Tests user data against check_credentials
        :param username: str submitted username <optional>
        :param password: str submitted password <optional>

        If either 'username' or 'password' is None, returns login form html

        If both are not None, fires check_credentials()

        Since ajax will always submit a value (even if an empty string), strings are
            returned to the browser to handle success/failure response.
        Any request with None as a value will be internal and will render the
            page in the browser.

        Returns str 'true' or 'false'
        '''

        if username is None or password is None:
            return self.login_form.default(username=username)

        # get origin ip
        if 'X-Forwarded-For' in cherrypy.request.headers:
            origin = cherrypy.request.headers['X-Forwarded-For']
        else:
            origin = cherrypy.request.headers['Remote-Addr']

        # on failed attempt
        if check_credentials(username, password) is False:
            log_attempt = 'Failed login attempt {}:{} from {}'.format(username, password, origin)

            logging.warning(log_attempt)

            return 'false'

        # on successful login
        else:
            try:
                cherrypy.session.regenerate()
            except Exception as e: # noqa
                pass
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = username
            self.on_login(username, origin)
            return 'true'

    @cherrypy.expose
    def logout(self):
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)
        raise cherrypy.InternalRedirect(core.URL_BASE + '/')

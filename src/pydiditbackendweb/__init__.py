import os
import requests
import ConfigParser
import simplejson as json
from datetime import datetime
import stat

default_ini_filename = os.path.expanduser('~/.pydidit-backendwebrc')

base_url = None
access_token_file_path = None

# A client front end must call check_initial_token()
# (or trade_initial_token()) to put a username in this global.
access_token = None


def initialize(ini_filenames=(default_ini_filename,)):
    ini = ConfigParser.SafeConfigParser()
    ini.read(ini_filenames)

    settings = dict(ini.items('backend'))

    global base_url
    if 'url' not in settings:
        raise Exception('"url" not available in settings.')
    base_url = settings['url']

    global access_token_file_path
    access_token_file_path = settings.get(
        'access_token_file',
        os.path.expanduser('~/.pydidit-cli-token')
    )


def encode_datetime(v):
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    raise TypeError


def decode_datetime(initial_result):
    for k, v in initial_result.iteritems():
        if isinstance(v, basestring):
            try:
                dt = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                pass
            else:
                initial_result[k] = dt
    return initial_result


def _send(f, args, kwargs):
    data = {
        'args': json.dumps(args, default=encode_datetime),
        'kwargs': json.dumps(kwargs, default=encode_datetime),
    }

    headers = {}
    if f in functions and functions[f]:
        headers['Authorization'] = 'Bearer {0}'.format(
            access_token
        )

    response = requests.post(
        '{0}/api/{1}'.format(base_url, f),
        json=data,
        headers=headers
    )
    if response.status_code != 200:
        raise RemoteException(response.status_code, response.text)
    return json.loads(response.json(), object_hook=decode_datetime)


function_template = '''def {function_name}(*args, **kwargs):
    return _send('{function_name}', args, kwargs)
'''


# Value shows whether authorization is required by the backend
functions = {
    'get': True,
    'get_like': True,
    'get_new_lowest_display_position': True,
    'make': True,
    'make_like': True,
    'add_to_db': True,
    'delete_from_db': True,
    'put': True,
    'put_like': True,
    'set_completed': True,
    'set_attributes': True,
    'link': True,
    'unlink': True,
    'flush': True,
    'relationship_name': True,
    'swap_display_positions': True,
    'move': True,
    'search': True,
    'get_users': True,
    'get_workspaces': True,
    'create_user': True,
    'create_workspace': True,
    'give_permission': True,
    'revoke_permission': True,
}

for function_name in functions.keys():
    exec function_template.format(function_name=function_name)

# Special cases

def commit(*args, **kwargs):
    pass

def check_initial_token(username, try_authed_call=True):
    # For now, store the access token in a 0600 file in $HOME.
    # If the file is there but not 0600, exit and warn the user.
    try:
        access_token_file_stat = os.stat(access_token_file_path)
    except OSError:
        # The client might want to do something special if the access token
        # file isn't there, as opposed to a later failure.  So we return None.
        return None

    if oct(access_token_file_stat.st_mode) != '0100600':
        raise TokenFileException('Your access token storage file must be mod 600.')

    global access_token
    with open(access_token_file_path, 'r') as fileh:
        access_tokens = json.load(fileh)

        if username not in access_tokens:
            return False

        access_token = access_tokens[username]

    if try_authed_call:
        try:
            get_users()
        except RemoteException:
            return None

    return True

def trade_initial_token(username, initial_token):
    response = requests.post(
        '{0}/trade'.format(base_url),
        json={
            'username': username,
            'initial_token': initial_token
        }
    )
    if response.status_code != 200:
        raise RemoteException(response.status_code, response.text)

    new_access_token = response.json()['access_token']
    tokens = {}
    # Access race here
    if check_initial_token(username) is not None:
        with open(access_token_file_path, 'r') as fileh:
            tokens = json.load(fileh)

    tokens[username] = new_access_token

    # Not locking the file, so potential collision here
    with open(access_token_file_path, 'w') as fileh:
        json.dump(tokens, fileh)
    # Enforce perms
    os.chmod(access_token_file_path, stat.S_IRUSR | stat.S_IWUSR)

# End special cases

class RemoteException(Exception):
    def __init__(self, code, text):
        self.code = code
        self.text = text

    def __str__(self):
        return '{0}: {1}'.format(self.code, self.text)

    def __repr__(self):
        return str(self)

class TokenFileException(Exception):
    pass

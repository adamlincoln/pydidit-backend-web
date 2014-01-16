import os
import requests
import ConfigParser
import simplejson as json
from datetime import datetime


base_url = None


def initialize(ini_filenames=(os.path.expanduser('~/.pydiditrc'),
                              os.path.expanduser('~/.pydidit-backendrc')),
               external_config_fp=None):
    ini = ConfigParser.SafeConfigParser()
    ini.read(ini_filenames)

    settings = dict(ini.items('backend'))

    global base_url
    base_url = settings['url']


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
        'f': f,
        'args': json.dumps(args, default=encode_datetime),
        'kwargs': json.dumps(kwargs, default=encode_datetime),
    }
    response = requests.post(base_url, data=data)
    if response.status_code != 200:
        raise RemoteException(response.status_code, response.text)
    return json.loads(response.text, object_hook=decode_datetime)


function_template = '''def {function_name}(*args, **kwargs):
    return _send('{function_name}', args, kwargs)
'''


for function_name in [
               'get',
               'get_like',
               'get_new_lowest_display_position',
               'make',
               'make_like',
               'add_to_db',
               'delete_from_db',
               'put',
               'put_like',
               'set_completed',
               'set_attributes',
               'link',
               'unlink',
               'flush',
               'relationship_name',
               'swap_display_positions',
               'move',
              ]:
    exec function_template.format(function_name=function_name)

# Special cases

def commit(*args, **kwargs):
    pass

# End special cases

class RemoteException(Exception):
    def __init__(self, code, text):
        self.code = code
        self.text = text

    def __str__(self):
        return '{0}: {1}'.format(self.code, self.text)

    def __repr__(self):
        return str(self)

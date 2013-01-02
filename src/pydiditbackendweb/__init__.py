import os
import requests
import ConfigParser
import simplejson as json


base_url = None


def initialize(ini_filenames=(os.path.expanduser('~/.pydiditrc'),
                              os.path.expanduser('~/.pydidit-backendrc')),
               external_config_fp=None):
    ini = ConfigParser.SafeConfigParser()
    ini.read(ini_filenames)

    settings = dict(ini.items('backend'))

    global base_url
    base_url = settings['url']


def _send(f, args, kwargs):
    data = {
        'f': f,
        'args': json.dumps(args),
        'kwargs': json.dumps(kwargs),
    }
    return json.loads(requests.post(base_url, data=data).text)


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
               'flush',
               'commit',
              ]:
    exec function_template.format(function_name=function_name)




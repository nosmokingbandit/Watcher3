#!/usr/bin/env python3
# ======================================== #
# ============= INSTRUCTIONS ============= #

# Copy this line to ~/.rtorrent.rc, replacing /PATH/TO/THIS/FILE.py with the actual file path.
# system.method.set_key = event.download.finished,Watcher,"execute={/usr/bin/python,/PATH/TO/THIS/FILE.py,\"$d.get_custom1=\",\"$d.get_name=\",\"$d.get_hash=\",\"$d.get_base_path=\"}"
#
# Add api information to conf:

watcherapi = 'APIKEY'
watcheraddress = u'http://localhost:9090/'
label = 'Watcher'

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #
import json
import sys
import urllib.request
import urllib.parse

data = {}

args = sys.argv

script, tor_label, name, downloadid, path = sys.argv

if label != tor_label:
    print('Label doesn\'t match config. Ignoring this download.')
    sys.exit(0)


while path[-1] in ['/', '\\']:
    path = path[:-1]

data['apikey'] = watcherapi

data['name'] = name
data['path'] = path
data['downloadid'] = downloadid
data['guid'] = downloadid
data['mode'] = 'complete'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urllib.parse.urlencode(data).encode('ascii')

request = urllib.request.Request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urllib.request.urlopen(request, timeout=600).read().decode('utf-8'))

if response['status'] == 'finished':
    sys.exit(0)
elif response['status'] == 'incomplete':
    sys.exit(1)
else:
    sys.exit(1)

sys.exit(0)

# pylama:ignore=E402

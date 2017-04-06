#!/usr/bin/env python3

# ======================================== #
# ============= INSTRUCTIONS ============= #

# Disable 'Post-Process Only Verified Jobs' in Sabnzbd.
# Add api information to conf:

conf = {
    'watcherapi': 'WATCHERAPIKEY',
    'watcheraddress': u'http://localhost:9090/',
    'sabkey': 'SABAPIKEY',
    'sabhost': 'localhost',
    'sabport': '8080'
}

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #

import json
import sys
import urllib.request
import urllib.parse

try:
    status = int(sys.argv[7])
    guid = sys.argv[3].replace('-', ':').replace('+', '/')
except:
    print('Post-processing failed. Incorrect args.')
    sys.exit(1)

watcheraddress = conf['watcheraddress']
watcherapi = conf['watcherapi']
sabkey = conf['sabkey']
sabhost = conf['sabhost']
sabport = conf['sabport']
data = {'apikey': watcherapi, 'guid': ''}

# get guid and nzo_id from sab history:
name = urllib.parse.quote(sys.argv[3], safe='')
url = u'http://{}:{}/sabnzbd/api?apikey={}&mode=history&output=json&search={}'.format(sabhost, sabport, sabkey, name)

request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(request, timeout=60).read().decode('utf-8')

slots = json.loads(response)['history']['slots']

for dl in slots:
    if dl['loaded'] is True:
        data['guid'] = dl['url']
        data['downloadid'] = dl['nzo_id']
        break

data['path'] = sys.argv[1]

# send it to Watcher
if status == 0:
    print('Sending {} to Watcher as Complete.'.format(name))
    data['mode'] = 'complete'
else:
    print('Sending {} to Watcher as Failed.'.format(name))
    data['mode'] = 'failed'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urllib.parse.urlencode(data).encode('ascii')

request = urllib.request.Request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})

response = json.loads(urllib.request.urlopen(request, timeout=600).read().decode('utf-8'))

if response.get('status') == 'finished':
    sys.exit(0)
else:
    sys.exit(1)

# pylama:ignore=E402

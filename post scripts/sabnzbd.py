#!/usr/bin/env python

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
import urllib
import urllib2

try:
    status = int(sys.argv[7])
    guid = sys.argv[3].replace('-', ':').replace('+', '/')
except:
    print u'Post-processing failed. Incorrect args.'
    sys.exit(1)

watcheraddress = conf['watcheraddress']
watcherapi = conf['watcherapi']
sabkey = conf['sabkey']
sabhost = conf['sabhost']
sabport = conf['sabport']
data = {'apikey': watcherapi, 'guid': ''}

# get guid and nzo_id from sab history:
name = urllib2.quote(sys.argv[3], safe='')
url = u'http://{}:{}/sabnzbd/api?apikey={}&mode=history&output=json&search={}'.format(sabhost, sabport, sabkey, name)

request = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib2.urlopen(request, timeout=60).read()

slots = json.loads(response)['history']['slots']

for dl in slots:
    if dl['loaded'] is True:
        data['guid'] = dl['url']
        data['downloadid'] = dl['nzo_id']
        break

data['path'] = sys.argv[1]

# send it to Watcher
if status == 0:
    print u'Sending {} to Watcher as Complete.'.format(name)
    data['mode'] = 'complete'
else:
    print u'Sending {} to Watcher as Failed.'.format(name)
    data['mode'] = 'failed'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urllib.urlencode(data)

request = urllib2.Request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})

response = json.loads(urllib2.urlopen(request, timeout=600).read())

if response.get('status') == 'finished':
    sys.exit(0)
else:
    sys.exit(1)

# pylama:ignore=E402

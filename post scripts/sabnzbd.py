#!/usr/bin/env python

# ======================================== #
# ============= INSTRUCTIONS ============= #

# Disable 'Post-Process Only Verified Jobs' in Sabnzbd.
# Add api information to conf:

conf = {
    'watcherapi': 'WATCHERAPIKEY',
    'watcheraddress': 'http://localhost:9090/',
    'sabkey': 'SABAPIKEY',
    'sabhost': 'localhost',
    'sabport': '8080',
    'verifyssl': True   # may need to change to False if using self-signed ssl cert
}

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #

import json
import sys
import ssl

if sys.version_info.major < 3:
    import urllib
    import urllib2
    urlencode = urllib.urlencode
    request = urllib2.Request
    urlopen = urllib2.urlopen
    urlquote = urllib.quote
else:
    import urllib.parse
    import urllib.request
    request = urllib.request.Request
    urlencode = urllib.parse.urlencode
    urlopen = urllib.request.urlopen
    urlquote = urllib.parse.quote

ctx = ssl.create_default_context()
if not conf['verifyssl']:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

# Gather info
try:
    status = int(sys.argv[7])
    guid = sys.argv[3].replace('-', ':').replace('+', '/')
except Exception:
    print('Post-processing failed. Incorrect args.')
    sys.exit(1)

watcheraddress = conf['watcheraddress']
watcherapi = conf['watcherapi']
sabkey = conf['sabkey']
sabhost = conf['sabhost']
sabport = conf['sabport']
data = {'apikey': watcherapi, 'guid': ''}

# get guid and nzo_id from sab history, since sab < 2.0 doesn't send with args:
name = urlquote(sys.argv[3], safe='')
url = u'http://{}:{}/sabnzbd/api?apikey={}&mode=history&output=json&search={}'.format(sabhost, sabport, sabkey, name)

req = request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urlopen(req, timeout=60, context=ctx).read().decode('utf-8')

slots = json.loads(response)['history']['slots']

for dl in slots:
    if dl['loaded'] is True:
        data['guid'] = dl['url']
        data['downloadid'] = dl['nzo_id']
        break

data['path'] = sys.argv[1]

if status == 0:
    print(u'Sending {} to Watcher as Complete.'.format(name))
    data['mode'] = 'complete'
else:
    print(u'Sending {} to Watcher as Failed.'.format(name))
    data['mode'] = 'failed'

# Send info
url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

req = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(req, timeout=600, context=ctx).read().decode('utf-8'))

if response.get('status') == 'finished':
    sys.exit(0)
else:
    sys.exit(1)

# pylama:ignore=E402

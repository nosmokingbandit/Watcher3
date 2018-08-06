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
verifyssl = True    # may need to change to False if using self-signed ssl cert

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #
import sys
script, rtor_label, name, downloadid, path = sys.argv

if label != rtor_label:
    print('Label doesn\'t match config. Ignoring this download.')
    sys.exit(0)

import json
import ssl

if sys.version_info.major < 3:
    import urllib
    import urllib2
    urlencode = urllib.urlencode
    request = urllib2.Request
    urlopen = urllib2.urlopen
else:
    import urllib.parse
    import urllib.request
    request = urllib.request.Request
    urlencode = urllib.parse.urlencode
    urlopen = urllib.request.urlopen

ctx = ssl.create_default_context()
if not verifyssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


# Gather info
data = {}

while path[-1] in ('/', '\\'):
    path = path[:-1]

data['apikey'] = watcherapi

data['name'] = name
data['path'] = path
data['downloadid'] = downloadid
data['guid'] = downloadid
data['mode'] = 'complete'

# Send info
url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

request = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(request, timeout=600, context=ctx).read().decode('utf-8'))

if response['status'] == 'finished':
    sys.exit(0)
elif response['status'] == 'incomplete':
    sys.exit(1)
else:
    sys.exit(1)

sys.exit(0)

# pylama:ignore=E402

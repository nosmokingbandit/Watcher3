#!/usr/bin/env python3
# ======================================== #
# ============= INSTRUCTIONS ============= #

# Add api information to conf:
watcherapi = 'apikey'
watcheraddress = 'http://localhost:9090/'

# Must use full path of download directory
destination = '/volume1/Downloads/Watcher'

# DownloadStation moves the downloaded file *after* calling this script, so we'll wait for it to complete.
# This can be increased if large files take longer to move to the final dir.
delay = 5

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #
import json
import os
import sys
import time

time.sleep(delay)

# Gather info
args = os.environ

if not args['TR_TORRENT_NAME'] in os.listdir(destination):
    # Not a Watcher download
    sys.exit(0)

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

data = {}
data['apikey'] = watcherapi
data['path'] = os.path.join(destination, args['TR_TORRENT_NAME'])
data['name'] = args['TR_TORRENT_NAME']
data['downloadid'] = args['TR_TORRENT_HASH']
data['guid'] = args['TR_TORRENT_HASH']
data['mode'] = 'complete'

# Send info
url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

request = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(request, timeout=600).read().decode('utf-8'))

if response['status'] == 'finished':
    sys.exit(0)
elif response['status'] == 'incomplete':
    sys.exit(1)
else:
    sys.exit(1)

sys.exit(0)


# pylama:ignore=E402

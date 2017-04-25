#!/usr/bin/env python3
# ======================================== #
# ============= INSTRUCTIONS ============= #

# Add file to Deluge's Execute plugin for event Torrent Complete

# Add api information to conf:

watcherapi = 'APIKEY'
watcheraddress = 'http://localhost:9090/'
category = 'Watcher'

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #

import json
import os
import sys

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

# Gather info
data = {}

args = sys.argv

download_dir = args[3]

while download_dir[-1] in ('/', '\\'):
    download_dir = download_dir[:-1]

parent_folder = os.path.split(download_dir)[-1]

if parent_folder.lower() != category.lower():
    # Not watcher category
    sys.exit(0)

data['apikey'] = watcherapi

data['name'] = args[2]
data['path'] = u'{}/{}'.format(download_dir, args[2])
data['downloadid'] = args[1]
data['guid'] = args[1]
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

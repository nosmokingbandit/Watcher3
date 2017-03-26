#!/usr/bin/env python
# ======================================== #
# ============= INSTRUCTIONS ============= #

# Add file to QBittorrent's Run External Program
# python "path/to/this/script/qbittorrent.py" "%N" "%D" "%R" "%I"

# Add api information to conf:

watcherapi = 'APIKEY'
watcheraddress = u'http://localhost:9090/'
category = 'Watcher'

#  DO NOT TOUCH ANYTHING BELOW THIS LINE!  #
# ======================================== #
import json
import os
import sys
import urllib
import urllib2

data = {}

args = sys.argv

download_dir = args[2]          # %D

while download_dir[-1] in ['/', '\\']:
    download_dir = download_dir[:-1]

parent_folder = os.path.split(download_dir)[-1]

if parent_folder.lower() != category.lower():
    # Not watcher category
    sys.exit(0)


data['apikey'] = watcherapi

data['name'] = args[1]          # %N
data['path'] = args[3]          # %R
data['downloadid'] = args[4]    # %I
data['guid'] = args[4]
data['mode'] = 'complete'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urllib.urlencode(data)

request = urllib2.Request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urllib2.urlopen(request, timeout=600).read())

if response['status'] == 'finished':
    sys.exit(0)
elif response['status'] == 'incomplete':
    sys.exit(1)
else:
    sys.exit(1)

sys.exit(0)

# pylama:ignore=E402

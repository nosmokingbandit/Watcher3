#!/usr/bin/env python3
# ========================================== #
# ============== INSTRUCTIONS ============== #
# === Used to test postprocessing script === #
# ========== Enter apikey and url ========== #
# ===== Run script as python3 test.py ====== #
# ========================================== #

watcherapi = ''
watcheraddress = ''

import json
import sys

if sys.version_info.major < 3:
    import urllib
    import urllib2
    urlencode = urllib.urlencode
    request = urllib2.Request
    urlopen = urllib2.urlopen
    input = raw_input
else:
    import urllib.parse
    import urllib.request
    request = urllib.request.Request
    urlencode = urllib.parse.urlencode
    urlopen = urllib.request.urlopen

data = {}

args = sys.argv

data['apikey'] = watcherapi or input('API Key: ')
download_dir = input('Download dir (parent of download): ')

while download_dir[-1] in ('/', '\\'):
    download_dir = download_dir[:-1]

guid = input('GUID: ')
name = input('Name: ')

data['downloadid'] = input('Downloadid (optional): ') or guid
data['name'] = name
data['path'] = u'{}/{}'.format(download_dir, name)
data['guid'] = guid
data['mode'] = 'complete'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

print('========================')
print('URL:')
print(url)
print('========================')
print('POST:')
print(post_data)
print('========================')

request = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(request, timeout=600).read().decode('utf-8'))

print(json.dumps(response, indent=4, sort_keys=True))

sys.exit(0)

# pylama:ignore=E402

#!/usr/bin/env python3
# ========================================== #
# ============== INSTRUCTIONS ============== #
# === Used to test postprocessing script === #
# ========== Enter apikey and url ========== #
# ===== Run script as python3 test.py ====== #
# ========================================== #

watcherapi = ''
watcheraddress = 'http://localhost:9090'
verifyssl = True    # may need to change to False if using self-signed ssl cert

import json
import sys
import os
import ssl

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

ctx = ssl.create_default_context()
if not verifyssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

data = {}

args = sys.argv

data['apikey'] = watcherapi or input('API Key: ')
download_dir = input('Download dir (parent of download): ')

while download_dir[-1] in ('/', '\\'):
    download_dir = download_dir[:-1]

guid = input('GUID: ')
name = input('Name (Folder name of download): ')

data['downloadid'] = input('Downloadid (optional): ') or guid
data['name'] = name
data['path'] = os.path.join(download_dir, name)
data['guid'] = guid
print('Mode:')
print('  1 Complete (default)')
print('  2 Failed')
mode = input('  [1, 2]: ')
data['mode'] = 'failed' if mode == '2' else 'complete'

url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

print('========================')
print('URL:')
print(url)
print('========================')
print('POST:')
print(json.dumps(data, indent=2))
print('========================')
print('Send Request?')
print('  Y Yes (default)')
print('  N No')
if input('  [Y, N]: ').lower() == 'n':
	sys.exit(0)

request = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(request, timeout=600, context=ctx).read().decode('utf-8'))

print(json.dumps(response, indent=2, sort_keys=True))

sys.exit(0)

# pylama:ignore=E402

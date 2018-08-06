#!/usr/bin/env python3

##########################################
######## DO NOT MODIFY THIS FILE! ########
## CONFIGURE API INFO THROUGH NZBGET UI ##
##########################################

#####################################
### NZBGET POST-PROCESSING SCRIPT ###

# Script to send post-processing info
# to Watcher.

#####################################
### OPTIONS                       ###

# Watcher API key.
#Apikey=

# Watcher address.
#Host=http://localhost:9090/


# Verify origin of Watcher's SSL certificate (enabled, disabled).
#  enabled    - Certificates must be valid (self-signed certs may fail)
#  disabled   - All certificates will be accepted
#VerifySSL=enabled

### NZBGET POST-PROCESSING SCRIPT ###
#####################################


import json
import os
import sys
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
if os.environ['NZBPO_VERIFYSSL'] != 'enabled':
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95

watcheraddress = os.environ['NZBPO_HOST']
watcherapi = os.environ['NZBPO_APIKEY']
name = os.environ['NZBPP_NZBNAME']
data = {'apikey': watcherapi, 'guid': ''}

# Gather info
if os.environ['NZBPP_URL']:
    data['guid'] = os.environ['NZBPP_URL']

data['downloadid'] = os.environ['NZBPP_NZBID']

data['path'] = os.environ['NZBPP_DIRECTORY']

if os.environ['NZBPP_TOTALSTATUS'] == 'SUCCESS':
    print(u'Sending {} to Watcher as Complete.'.format(name))
    data['mode'] = 'complete'
else:
    print(u'Sending {} to Watcher as Failed.'.format(name))
    data['mode'] = 'failed'

# Send info
url = u'{}/postprocessing/'.format(watcheraddress)
post_data = urlencode(data).encode('ascii')

request = request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urlopen(request, timeout=600, context=ctx).read().decode('utf-8'))

if response.get('status') == 'finished':
    sys.exit(POSTPROCESS_SUCCESS)
elif response.get('status') == 'incomplete':
    sys.exit(POSTPROCESS_ERROR)
else:
    sys.exit(POSTPROCESS_NONE)

# pylama:ignore=E266,E265

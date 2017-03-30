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

### NZBGET POST-PROCESSING SCRIPT ###
#####################################

import json
import os
import sys
import urllib.request
import urllib.parse

POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95

watcherhost = os.environ['NZBPO_HOST']
watcherapi = os.environ['NZBPO_APIKEY']
name = os.environ['NZBPP_NZBNAME']
data = {'apikey': watcherapi, 'guid': ''}

# can be blank it from an uploaded nzb file
if os.environ['NZBPP_URL']:
    data['guid'] = os.environ['NZBPP_URL']

data['downloadid'] = os.environ['NZBPP_NZBID']

data['path'] = os.environ['NZBPP_DIRECTORY']

# set the post-processing mode
if os.environ['NZBPP_TOTALSTATUS'] == 'SUCCESS':
    print('Sending {} to Watcher as Complete.'.format(name))
    data['mode'] = 'complete'
else:
    print('Sending {} to Watcher as Failed.'.format(name))
    data['mode'] = 'failed'

url = u'{}/postprocessing/'.format(watcherhost)
post_data = urllib.parse.urlencode(data).encode('ascii')

request = urllib.request.Request(url, post_data, headers={'User-Agent': 'Mozilla/5.0'})
response = json.loads(urllib.request.urlopen(request, timeout=600).read())

if response.get('status') == 'finished':
    sys.exit(POSTPROCESS_SUCCESS)
elif response.get('status') == 'incomplete':
    sys.exit(POSTPROCESS_ERROR)
else:
    sys.exit(POSTPROCESS_NONE)

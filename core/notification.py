import core
import logging
import json

logging = logging.getLogger(__name__)


class Notification(object):

    def __init__(self):
        return

    @staticmethod
    def add(data):
        ''' Adds notification to core.NOTIFICATIONS
        :param data: dict of notification information

        Merges supplied 'data' with 'base' dict to ensure no fields are missing
        Appends 'base' to core.NOTIFICATIONS

        If data['param'] includes an on_click function, remember to add it to the
            notifications javascript handler.

        Does not return
        '''

        base = {'type': 'success',
                'title': '',
                'body': '',
                'params': None
                }

        base.update(data)

        logging.debug('Creating new notification:')
        logging.debug(base)

        # if it already exists, ignore it
        if base in core.NOTIFICATIONS:
            return

        # if this is an update notif, remove other update notifs first
        if base['type'] == 'update':
            for i, v in enumerate(core.NOTIFICATIONS):
                if v['type'] == 'update':
                    core.NOTIFICATIONS[i] = None

        # if there is a None in the list, overwrite it. If not, just append
        for i, v in enumerate(core.NOTIFICATIONS):
            if v is None:
                core.NOTIFICATIONS[i] = base
                return
        core.NOTIFICATIONS.append(base)

        return

    @staticmethod
    def remove(index):
        ''' Removes notification from core.notification
        :param index: int index of notification to remove

        Replaces list item with None as to not affect other indexes.

        When adding new notifs through core.notification, any None values
            will be overwritten before appending to the end of the list.
        Removes all trailing 'None' entries in list.

        This ensures the list will always be as small as possible without
            changing existing indexes.

        Does not return
        '''

        logging.debug('Remove notification #{}.'.format(index))
        core.NOTIFICATIONS[int(index)] = None

        logging.debug('Cleaning notification queue.')
        while len(core.NOTIFICATIONS) > 0 and core.NOTIFICATIONS[-1] is None:
            core.NOTIFICATIONS.pop()

        return


'''
NOTIFICATION dict:

'icon': None,       str font awesome icon 'fa-star'
'title': None,      str large title text 'Something Happened!'
'title_link': None, str url for title to link to.
'text': None,       str main body text explaining title if necessary
'button': None      tuple ('Name', '/url/link' , 'fa-refresh')

All Ajax  requests should be specified in static/notifications/main.js

'''

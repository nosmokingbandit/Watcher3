import core
import logging

logging = logging.getLogger(__name__)


def add(data, type_='success'):
    ''' Adds notification to core.NOTIFICATIONS
    data (dict): notification information
    type_ (str): style of notification, see javascript docs for available styles    <optional - default 'success'>

    Merges supplied 'data' with 'options' dict to ensure no fields are missing
    Appends notif to core.NOTIFICATIONS

    Notif structure is tuple of two dicts. [0] containing 'options' dict and [1] with 'settings' dict

    Does not return
    '''

    logging.info('Adding notification to queue.')

    options = {'title': '',
               'message': '',
               'type': None
               }

    settings = {'type': type_,
                'delay': 0
                }

    options.update(data)

    logging.debug(options)

    # if it already exists, ignore it
    if options in core.NOTIFICATIONS:
        return

    # if this is an update notif, remove other update notifs first
    if options['type'] == 'update':
        for i, v in enumerate(core.NOTIFICATIONS):
            if v[0]['type'] == 'update':
                core.NOTIFICATIONS[i] = None

    new_notif = [options, settings]

    # if there is a None in the list, overwrite it. If not, just append
    for i, v in enumerate(core.NOTIFICATIONS):
        if v is None:
            new_notif[1]['index'] = i
            core.NOTIFICATIONS[i] = new_notif
            return

    new_notif[1]['index'] = len(core.NOTIFICATIONS)
    core.NOTIFICATIONS.append(new_notif)

    return


def remove(index):
    ''' Removes notification from core.NOTIFICATIONS
    index (int): index of notification to remove

    Replaces list item with None as to not affect other indexes.

    When adding new notifs through core.notification, any None values
        will be overwritten before appending to the end of the list.
    Removes all trailing 'None' entries in list.

    This ensures the list will always be as small as possible without
        changing existing indexes.

    Does not return
    '''

    logging.info('Remove notification #{}.'.format(index))
    try:
        core.NOTIFICATIONS[int(index)] = None
    except Exception as e:
        pass

    logging.debug('Cleaning notification queue.')
    while len(core.NOTIFICATIONS) > 0 and core.NOTIFICATIONS[-1] is None:
        core.NOTIFICATIONS.pop()

    return

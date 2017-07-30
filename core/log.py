import logging
import logging.handlers
import os

import core

'''
Logging rules:

Every function/method call should start with a log entry unless it simply calls another function that enters its own log

'''


def start(path):
    ''' Starts logging service
    path (str): absolute path to log directory

    Does not return
    '''

    if not os.path.exists(path):
        os.makedirs(path)

    logfile = os.path.join(path, 'log.txt')
    backup_days = core.CONFIG['Server']['keeplog']
    logging_level = logging.DEBUG

    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s.%(funcName)s: %(message)s')
    handler = logging.handlers.TimedRotatingFileHandler(logfile, when="D", interval=1, backupCount=backup_days, encoding='utf-8')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging_level)

    return

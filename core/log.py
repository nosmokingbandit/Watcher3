import logging
import logging.handlers
import os

import core

'''
Logging rules:

Every function/method call should start with a log entry unless it simply calls another function that enters its own log

'''


def start(path, stdout=False):
    ''' Starts logging service
    path (str): absolute path to log directory
    stdout (bool): enable writing of all log entries to stdout as well as the log file <default False>

    Does not return
    '''

    if not os.path.exists(path):
        os.makedirs(path)

    logger = logging.getLogger()
    logger.setLevel(0)

    logfile = os.path.join(path, 'log.txt')

    formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(name)s.%(funcName)s.%(lineno)s: %(message)s')

    file_handler = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=core.CONFIG['Server']['keeplog'], encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(0 if core.CONFIG['Server']['debuglog'] else 20)

    logger.addHandler(file_handler)

    if stdout:
        term_handler = logging.StreamHandler()
        term_handler.setFormatter(formatter)
        term_handler.setLevel(0)
        logger.addHandler(term_handler)

    return

import core
import json
import os
import sys
import operator
import subprocess
import threading
import logging

logging = logging.getLogger(__name__)


def list_plugins():
    ''' Finds all plugins in folder

    Returns dict {'added': [('plugin.py', 'config.conf')], 'snatched': [('plugin.py', None)], 'finished': []}
    '''

    plugins = {'added': [], 'snatched': [], 'finished': []}

    for folder in plugins.keys():
        try:
            p_dir = os.path.join(core.PLUGIN_DIR, folder)

            a = [i for i in os.listdir(p_dir) if i.endswith('.py') and not i.startswith('.')]

            for p in a:
                c_file = '{}.conf'.format(p[:-3])
                c = c_file if os.path.isfile(os.path.join(p_dir, c_file)) else None
                plugins[folder].append((p, c))

        except Exception as e:
            logging.error('Unable to read {} plugins folder'.format(folder), exc_info=True)

    return plugins


def added(*args):
    ''' Executes added plugins
    *args (list): arguments to pass to plugins

    args should contain: title, year, imdbid, quality

    Does not return
    '''

    plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'added')

    sorted_plugins = sorted(core.CONFIG['Plugins']['added'].items(), key=operator.itemgetter(1))

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

    threading.Thread(target=execute, args=(plugins, args)).start()

    return


def snatched(*args):
    ''' Executes snatched plugins
    *args (list): arguments to pass to plugins

    args should contain: title, year, imdbid, resolution, kind, downloader, downloadid, indexer, info_link

    Does not return
    '''

    plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'snatched')

    sorted_plugins = sorted(core.CONFIG['Plugins']['snatched'].items(), key=operator.itemgetter(1))

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

    threading.Thread(target=execute, args=(plugins, args)).start()

    return


def finished(*args):
    ''' Executes finished plugins
    *args (list): arguments to pass to plugins

    args shoudl contain: title, year, imdbid, resolution, rated, original_file, new_file_location, downloadid, finished_date

    Does not return
    '''

    plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'finished')

    sorted_plugins = sorted(core.CONFIG['Plugins']['finished'].items(), key=operator.itemgetter(1))

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

    threading.Thread(target=execute, args=(plugins, args)).start()

    return


def execute(plugins, args):
    ''' Executes a list of plugins
    plugins (list): *absolute* paths to plugins
    args (list): args to pass to plugin

    Does not return
    '''

    args = list(args)

    for plugin in plugins:
        conf_file = '{}.conf'.format(os.path.splitext(plugin)[0])

        try:
            if os.path.isfile(conf_file):
                with open(conf_file) as f:
                    args.append(json.dumps(json.load(f)))
        except Exception as e:
            logging.error('Loading config {} failed.'.format(conf_file), exc_info=True)
            continue

        command = [sys.executable, plugin] + args
        if core.PLATFORM == 'windows':
            cmd = ['cmd', '/c']
            command = cmd + command
        command = [str(i) for i in command]
        name = os.path.split(plugin)[1]

        try:
            logging.debug('Executing plugin {} as {}.'.format(name, command))

            process = subprocess.Popen(command,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=False,
                                       cwd=core.PROG_PATH
                                       )
            output, error = process.communicate()
            exit_code = process.returncode

            for line in output.splitlines():
                logging.info('{} - {}'.format(name, line))
            if exit_code == 0:
                logging.info('{} - Execution finished. Exit code {}.'.format(name, '0'))
            else:
                logging.warning('{} - Execution failed. Exit code {}.'.format(name, exit_code))

        except Exception as e:
            logging.error('Executing plugin {} failed.'.format(plugin), exc_info=True)
            continue

    return

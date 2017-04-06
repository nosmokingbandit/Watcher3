import core
import json
import os
import sys
import operator
import subprocess
import threading
import logging

logging = logging.getLogger(__name__)


class Plugins(object):

    def added(self, *args):
        # title, year, imdbid, quality

        plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'added')

        sorted_plugins = sorted(core.CONFIG['Plugins']['added'].items(), key=operator.itemgetter(1))

        plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

        t = threading.Thread(target=self.execute,
                             args=(plugins, args))
        t.start()

        return

    def snatched(self, *args):
        # title, year, imdbid, resolution, kind, downloader, downloadid, indexer, info_link

        plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'snatched')

        sorted_plugins = sorted(core.CONFIG['Plugins']['snatched'].items(), key=operator.itemgetter(1))

        plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

        t = threading.Thread(target=self.execute,
                             args=(plugins, args))
        t.start()

        return

    def finished(self, *args):
        # title, year, imdbid, resolution, rated, original_file, new_file_location, downloadid, finished_date

        plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'finished')

        sorted_plugins = sorted(core.CONFIG['Plugins']['finished'].items(), key=operator.itemgetter(1))

        plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins]

        t = threading.Thread(target=self.execute,
                             args=(plugins, args))
        t.start()

        return

    def execute(self, plugins, args):
        ''' Executes a list of plugins
        plugins: list of *absolute* paths to plugins
        args: list or tuple of args to pass to plugin

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
            if os.name == 'nt':
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

            except Exception as e: #noqa
                logging.error('Executing plugin {} failed.'.format(plugin), exc_info=True)
                continue

        return

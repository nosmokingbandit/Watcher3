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


def render_config(config):
    ''' Generates config html for plugins
    config (dict): contents of plugin config

    Returns str html form
    '''

    html = ''

    if config.pop('Config Version', 0) < 2:
        for k, v in config.items():
            html += '''
            <div class="col-md-6" data-type="string">
                <label>{0}</label>
                <input type="text" class="form-control" data-key="{0}" value="{1}">
            </div>
            '''.format(k, v)

    else:
        inputs = []
        for name, c in config.items():
            c['name'] = name
            inputs.append(c)

        for i in sorted(inputs, key=lambda x: x.get('display', 0)):
            if i['type'] == 'string':
                html += _config_string(i)
            elif i['type'] == 'int':
                html += _config_int(i)
            elif i['type'] == 'bool':
                html += _config_bool(i)

    return html


''' The next group of private methods all generate the actual html for a V2 config file
All take one argument, config (dict), which is a dictionary of the config for that datatype

All return a string of html
'''


def _config_string(config):

    base = {'label': '&nbsp',
            'helptext': '',
            'value': ''
            }

    base.update(config)
    try:
        return '''
        <div class="col-md-6" data-type="string" title="{helptext}">
            <label>{label}</label>
            <input type="text" class="form-control" data-key="{name}" value="{value}">
        </div>
        '''.format(**base)
    except Exception as e:
        logging.warning('Unable to parse plugin config.', exc_info=True)
        return ''


def _config_int(config):

    base = {'label': '&nbsp',
            'helptext': '',
            'value': '',
            'min': '',
            'max': ''
            }

    base.update(config)
    try:
        return '''
        <div class="col-md-6" data-type="int" title="{helptext}">
            <label>{label}</label>
            <input type="number" class="form-control" data-key="{name}" value="{value}" min="{min}" max="{max}">
        </div>
        '''.format(**base)
    except Exception as e:
        logging.warning('Unable to parse plugin config.', exc_info=True)
        return ''


def _config_bool(config):

    base = {'label': '&nbsp',
            'helptext': '',
            'value': False
            }

    base.update(config)
    try:
        return '''
        <div class="col-md-6" data-type="bool" title="{helptext}">
            <label>&nbsp;</label>
            <div class="input-group">
                <span class="input-group-addon box_box">
                <i class="mdi mdi-checkbox-blank-outline c_box" data-key="{name}" value="{value}"></i>
                </span>
                <span class="input-group-item form-control _label">
                    {label}
                </span>
            </div>
        </div>
        '''.format(**base)
    except Exception as e:
        logging.warning('Unable to parse plugin config.', exc_info=True)
        return ''


def added(*args):
    ''' Executes added plugins
    *args (list): arguments to pass to plugins

    args should contain: title, year, imdbid, quality

    Does not return
    '''

    plugin_dir = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, 'added')

    sorted_plugins = sorted(core.CONFIG['Plugins']['added'].items(), key=operator.itemgetter(1))

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins if i[1][0]]

    if plugins:
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

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins if i[1][0]]

    if plugins:
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

    plugins = [os.path.join(plugin_dir, i[0]) for i in sorted_plugins if i[1][0]]

    if plugins:
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
                    config = json.load(f)
                    if config.pop('Config Version', 0) > 1:
                        config = {i: config[i]['value'] for i in config}
            else:
                config = {}
        except Exception as e:
            logging.error('Loading config {} failed.'.format(conf_file), exc_info=True)
            continue

        config = json.dumps(config)

        command = [sys.executable, plugin] + args
        command.append(config)

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

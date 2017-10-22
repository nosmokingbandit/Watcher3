import backup
import datetime
import json
import logging
import os
import shutil
import subprocess
import zipfile

import core
from core import notification
from core.helpers import Url

logmodule = logging
logging = logging.getLogger(__name__)


def manager():
    ''' Gets instance of update manager

    Returns obj class instance of manager (Git or Zip)
    '''

    return GitUpdater('master') if os.path.exists('.git') else ZipUpdater('master')


class UpdateBase(object):
    ''' Base class for updater instances '''

    def update_check(self, add_notif=True, install=True):
        logging.info('Checking for updates.')
        data = self._update_check()
        # if data['status'] == 'current', nothing to do.
        if data['status'] == 'error':
            notif = {'title': 'Error Checking for Updates <br/>',
                     'message': data['error']
                     }
            notification.add(notif, type_='danger')

        elif data['status'] == 'behind':
            if data['behind_count'] == 1:
                title = '1 Update Available <br/>'
            else:
                title = '{} Updates Available <br/>'.format(data['behind_count'])

            compare = '{}/compare/{}...{}'.format(core.GIT_URL, data['local_hash'], data['new_hash'])

            notif = {'type': 'update',
                     'title': title,
                     'message': 'Click <a onclick="_start_update(event)"><u>here</u></a> to update now.<br/> Click <a href="{}" target="_blank" rel="noopener"><u>here</u></a> to view changes.'.format(compare)
                     }

            notification.add(notif, type_='success')

            if install and core.CONFIG['Server']['installupdates']:
                logging.info('Currently {} commits behind. Updating to {}.'.format(core.UPDATE_STATUS['behind_count'], core.UPDATE_STATUS['new_hash']))

                core.UPDATING = True
                core.scheduler_plugin.stop()
                update = self.execute_update()
                core.UPDATING = False

                if not update:
                    logging.error('Update failed.')
                    core.scheduler_plugin.restart()

                logging.info('Update successful, restarting.')
                core.restart()
            else:
                logging.info('Currently {} commits behind. Automatic install disabled'.format(core.UPDATE_STATUS['behind_count']))

        return data


class Git(object):
    ''' Class used to execute all GIT commands. '''

    def runner(self, args):
        ''' Runs all git commmands.
        args (str): git command line arguments, space delimited

        Execcutes args as command line arguments via subprocess

        error message in return tuple is None if everything went well

        Returns tuple: (bytestring output, str error message, int exit_status)
        '''

        CREATE_NO_WINDOW = 0x08000000

        command = [core.CONFIG['Server']['gitpath'] or 'git']
        for i in args.split(' '):
            command.append(i)

        logging.debug('Executing Git command: {}'.format(command))

        try:
            if core.PLATFORM == 'windows':
                p = subprocess.Popen(command,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     shell=False,
                                     cwd=core.PROG_PATH,
                                     creationflags=CREATE_NO_WINDOW
                                     )
            else:
                p = subprocess.Popen(command,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     shell=False,
                                     cwd=core.PROG_PATH
                                     )
            output, error = p.communicate()
            exit_status = p.returncode
            return (output.decode('utf-8').rstrip(), error, exit_status)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Subprocess error.', exc_info=True)
            err = str(e)
            return (err, 'Subprocess error.', 1)

    def get_current_hash(self):
        ''' Gets current commit hash

        Returns tuple: (str hash, str error, int exit_code)
        '''
        logging.debug('Retreiving local commit hash.')
        command = 'rev-parse HEAD'
        output, error, status = self.runner(command)
        return (output, error, status)

    def get_commit_hash_history(self):
        ''' Gets hash history

        Returns tuple: (list hash history, str error, int exit_status)
        '''
        logging.debug('Retreiving commit hash history.')
        command = 'rev-list @{u}'
        output, error, status = self.runner(command)
        output = output.splitlines()
        return (output, error, status)

    def available(self):
        ''' Checks to see if we can execute git.

        Returns: tuple (str git version, str error, int exit_status)
        '''
        logging.debug('Checking Git execution permission.')

        command = 'version'
        output, error, status = self.runner(command)
        output = output.splitlines()
        return (output, error, status)

    def fetch(self):
        ''' Gathers new branch information

        Returns: tuple (str b'', str error, int exit_status)
        '''
        logging.debug('Fetching latest Git info.')
        command = 'fetch'
        output, error, status = self.runner(command)
        return (output, error, status)

    def pull(self):
        ''' Merges remote branch with local

        Returns: tuple (str merge result, str error, int exit_status)
        '''
        logging.debug('Pulling latest commit.')
        command = 'pull'
        output, error, status = self.runner(command)
        return (output, error, status)


class GitUpdater(UpdateBase):

    def __init__(self, branch):
        logging.debug('Setting updater to Git.')
        self.git = Git()

        if self._git_available:
            self.current_hash = self.git.get_current_hash()
            core.CURRENT_HASH = self.current_hash[0]
        return

    def _git_available(self):
        ''' Tests ability to execute Git commands

        Returns bool
        '''
        git_available = self.git.available()
        if git_available[2] == 1:
            logging.error('Could not execute git: {}'.format(git_available[0]))
            return False
        else:
            return True

    def execute_update(self):
        ''' Performs update process

        Runs git.fetch(), git.pull()

        Returns bool
        '''
        logging.info('Updating from Git.')

        fetch = self.git.fetch()
        if fetch[2] == 1:
            logging.error('Error fetching data from git: {}'.format(fetch[1]))
            return False

        # reset update status so it doesn't ask us to update again
        core.UPDATE_STATUS = None

        pull = self.git.pull()

        if pull[2] == 1:
            logging.error('Update failed: {}'.format(pull[0]))
            return False
        else:
            logging.info('Update successful.')
            return True

    def _update_check(self):
        ''' Gets commit delta from GIT.

        Sets core.UPDATE_STATUS to return value.
        Returns dict:
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        core.UPDATE_LAST_CHECKED = datetime.datetime.now()

        result = {}

        if not self._git_available():
            result['status'] = 'error'
            result['error'] = 'Unable to execute Git commands.'
            core.UPDATE_STATUS = result
            return result

        # Make sure our git info is up to date
        fetch = self.git.fetch()
        if fetch[2] == 1:
            logging.error('Error fetching data from git: {}'.format(fetch[1]))
            result['status'] = 'error'
            result['error'] = fetch[1]
            core.UPDATE_STATUS = result
            return result

        # check if we got a valid local hash
        if self.current_hash[2] == 1:
            logging.error('Error getting local commit hash: {}'.format(self.current_hash[1]))
            result['status'] = 'error'
            result['error'] = self.current_hash[1]
            core.UPDATE_STATUS = result
            return result
        local_hash = self.current_hash[0]
        logging.info('Current local hash: {}'.format(local_hash))

        # try to get a history of commit hashes
        commit_history = self.git.get_commit_hash_history()
        if commit_history[2] == 1:
            logging.error('Error getting git commit history: {}'.format(commit_history[1]))
            result['status'] = 'error'
            result['error'] = commit_history[1]
            core.UPDATE_STATUS = result
            return result
        commit_list = commit_history[0]

        # make sure our hash is in the history
        if local_hash in commit_list:
            behind_count = commit_list.index(local_hash)
            # if it is the first result we are up to date
            if behind_count == 0:
                logging.debug('Watcher is up to date.')
                result['status'] = 'current'
                core.UPDATE_STATUS = result
                return result
            # if not, find out how far behind we are
            else:
                logging.debug('{} updates are available -- latest commit: {}.'.format(behind_count, commit_list[0]))

                result['status'] = 'behind'
                result['behind_count'] = behind_count
                result['local_hash'] = local_hash
                result['new_hash'] = commit_list[0]
                core.UPDATE_STATUS = result
                logging.info('Update found:')
                logging.info(result)
                return result
        else:
            logging.error('Current local hash not in git history.')
            result['status'] = 'error'
            result['error'] = 'Current local hash not in git history.'
            core.UPDATE_STATUS = result
            return result


class ZipUpdater(UpdateBase):
    ''' Manager for updates install without git.

    Updates by downloading the new zip from github. Uses backup.py to
        backup and restore user's files.
    '''

    def __init__(self, branch):
        logging.debug('Setting updater to Zip.')
        self.branch = branch
        self.version_file = os.path.join('core', 'version')
        self.current_hash = self.get_current_hash()
        core.CURRENT_HASH = self.current_hash
        return

    def get_current_hash(self):
        ''' Gets current commit hash.

        If file watcher/core/version exists, reads hash from file
        If not, gets newest hash from GIT and creates version file

        Sets core.CURRENT_HASH as current commit hash

        Returns str current hash version
        '''
        logging.debug('Retreiving local commit hash.')

        if os.path.isfile(self.version_file):
            with open(self.version_file, 'r') as f:
                hash = f.read()
            return hash
        else:
            new_hash = self.get_newest_hash()
            if new_hash:
                with open(self.version_file, 'w') as f:
                    f.write(new_hash)
        core.CURRENT_HASH = new_hash
        return new_hash

    def get_newest_hash(self):
        ''' Gets latest version hash from Github

        Returns str
        '''
        url = '{}/commits/{}'.format(core.GIT_API, self.branch)
        try:
            result = json.loads(Url.open(url).text)
            return result['sha']
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Could not get newest hash from git.', exc_info=True)
            return ''

    def _update_check(self):
        ''' Gets commit delta from Github

        Sets core.UPDATE_STATUS to return value

        Returns dict:
            {'status': 'error', 'error': <error> }
            {'status': 'behind', 'behind_count': #, 'local_hash': 'abcdefg', 'new_hash': 'bcdefgh'}
            {'status': 'current'}
        '''

        os.chdir(core.PROG_PATH)
        core.UPDATE_LAST_CHECKED = datetime.datetime.now()

        result = {}

        local_hash = self.current_hash
        if not local_hash:
            logging.warning('Unable to check for updates, current hash is unknown.')
            result['status'] = 'error'
            result['error'] = 'Could not get local hash. Check logs for details.'
            core.UPDATE_STATUS = result
            return result

        newest_hash = self.get_newest_hash()
        if not newest_hash:
            result['status'] = 'error'
            result['error'] = 'Could not get latest update hash. Check logs for details.'
            core.UPDATE_STATUS = result
            return result

        url = '{}/compare/{}...{}'.format(core.GIT_API, newest_hash, local_hash)

        try:
            result = json.loads(Url.open(url).text)
            behind_count = result['behind_by']
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            logging.error('Could not get update information from git.', exc_info=True)
            result['status'] = 'error'
            result['error'] = 'Could not get update information from git.'
            core.UPDATE_STATUS = result
            return result

        if behind_count == 0:
            logging.debug('Watcher is up to date.')
            result['status'] = 'current'
            core.UPDATE_STATUS = result
            return result
        else:
            logging.debug('{} updates are available -- latest commit: {}.'.format(behind_count, newest_hash))

            result['status'] = 'behind'
            result['behind_count'] = behind_count
            result['local_hash'] = local_hash
            result['new_hash'] = newest_hash
            core.UPDATE_STATUS = result
            return result

    def switch_log(self, handler):
        ''' Changes log path to tmp file
        handler (object): log handler object instance

        Used to move amd restore open log file so it can be overwritten
            if neccesay during update.

        Returns object current log handler object (prior to running this method)
        '''

        import logging.handlers

        log = logging.getLogger()  # root logger
        for hdlr in log.handlers[:]:  # remove all old handlers
            original = hdlr
            hdlr.close()
            log.removeHandler(hdlr)
        log.addHandler(handler)      # set the new handler
        return original

    def execute_update(self):
        ''' Performs update process

        Creates temporary directory to store update files
        Downloads zip from github and extracts
        Switches log handler log location in update dir
        Backs up user's files
        Overwrites all files with files from zip
        Restores user's files
        Appends temporary log to original log file
        Retores original log handler
        Removes temporary dir

        Returns bool
        '''
        logging.info('Updating from Zip file.')

        os.chdir(core.PROG_PATH)
        update_zip = 'update.zip'
        update_path = 'update'
        new_hash = self.get_newest_hash()

        logging.info('Cleaning up old update files.')
        try:
            if os.path.isfile(update_zip):
                os.remove(update_zip)
            if os.path.isdir(update_path):
                shutil.rmtree(update_path)
            os.mkdir(update_path)
        except Exception as e:
            logging.error('Could not delete old update files.', exc_info=True)
            return False

        logging.info('Creating temporary update log file.')
        formatter = logmodule.Formatter('%(levelname)s %(asctime)s %(name)s.%(funcName)s: %(message)s')
        handler = logmodule.FileHandler(os.path.join(update_path, 'log.txt'), 'a')
        handler.setFormatter(formatter)
        logging.debug('Switching to temporary log handler while updating.')
        orig_log_handler = self.switch_log(handler)

        logging.info('Downloading latest Zip.')
        zip_url = '{}/archive/{}.zip'.format(core.GIT_URL, self.branch)
        try:
            zip_bytes = Url.open(zip_url, stream=True).content
            with open(update_zip, 'wb') as f:
                f.write(zip_bytes)
            del zip_bytes
        except Exception as e:
            logging.error('Could not download latest Zip.', exc_info=True)
            return False

        logging.info('Extracting Zip to temporary directory.')
        try:
            with zipfile.ZipFile(update_zip) as f:
                f.extractall(update_path)
        except Exception as e:
            logging.error('Could not extract Zip.', exc_info=True)
            return False

        logging.info('Backing up user\'s files.')
        backup.backup(require_confirm=False)

        # reset update status so it doesn't ask us to update again
        core.UPDATE_STATUS = None

        logging.info('Moving update files.')
        subfolder = 'Watcher3-{}'.format(self.branch)
        update_files_path = os.path.join(update_path, subfolder)
        try:
            files = os.listdir(update_files_path)
            for file in files:
                src = os.path.join(update_files_path, file)
                dst = file

                if os.path.isfile(src):
                    if os.path.isfile(dst):
                        os.remove(dst)
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
        except Exception as e:
            logging.error('Could not move update files.', exc_info=True)
            return False

        logging.info('Restoring user files.')
        backup.restore(require_confirm=False)

        logging.info('Setting new version file.')
        try:
            with open(self.version_file, 'w') as f:
                    f.write(new_hash)
        except Exception as e:
            logging.error('Could not update version file.', exc_info=True)
            return False

        logging.info('Merging update log with master.')
        with open(orig_log_handler.baseFilename, 'a') as log:
            with open(os.path.join(update_path, 'log.txt'), 'r') as u_log:
                log.write(u_log.read())

        logging.info('Changing log handler back to original.')
        self.switch_log(orig_log_handler)

        logging.info('Cleaning up temporary files.')
        try:
            shutil.rmtree(update_path)
            os.remove(update_zip)
        except Exception as e:
            logging.error('Could not delete temporary files.', exc_info=True)
            return False

        logging.info('Update successful.')
        return True

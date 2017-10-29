import argparse
import os
import shutil
import sys
import zipfile


def backup(require_confirm=True):
    # create backup zip
    print('Creating watcher.zip')
    shutil.make_archive('watcher', 'zip', 'userdata')

    print('**############################################################**')
    print('**##################### Backup finished ######################**')
    print('**################# Zip backup: watcher.zip ##################**')
    print('**############################################################**')

    return


def restore(require_confirm=True, file='watcher.zip'):

    if not os.path.isfile(file):
        print('watcher.zip not found. Place watcher.zip in same directory as backup script.')
        return

    if require_confirm is True:
        ans = input('Restoring backup. This will overwrite existing '
                    'database, config, and posters. Continue? (y/N):  ')
        if ans.lower() != 'y':
            return

    if os.path.isdir('userdata'):
        print('Removing existing userdata folder.')
        shutil.rmtree('userdata')

    print('Extracting zip.')
    zipf = zipfile.ZipFile(file)
    zipf.extractall('userdata')

    print('**############################################################**')
    print('**##################### Restore finished #####################**')
    print('**################# Zip backup: watcher.zip ##################**')
    print('**############################################################**')

    return


if __name__ == '__main__':

    print('**############################################################**')
    print('**############### Watcher backup/restore tool ################**')
    print('** Confirm that Watcher is not running while restoring backup **')
    print('**############################################################**')

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    cwd = os.getcwd()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--backup', help='Back up to watcher.zip.', action='store_true')
    group.add_argument('-r', '--restore', help='Restore from watcher.zip.', action='store_true')
    group.add_argument('-y', '--confirm', help='Ignore warnings and answer Y to prompts.', action='store_true')
    args = parser.parse_args()

    if args.confirm:
        require_confirm = False
    else:
        require_confirm = True

    if args.backup:
        backup(require_confirm)
        sys.exit(0)
    elif args.restore:
        restore(require_confirm)
        sys.exit(0)
    else:
        print('Invalid arguments.')
        sys.exit(0)

## Watcher

Watcher is an automated movie NZB & Torrent searcher and snatcher. You can add a list of wanted movies and Watcher will automatically send the NZB or Torrent to your download client. Watcher also has basic post-processing capabilities such as renaming and moving.

Watcher is a work in progress and plans to add more features in the future, but we will always prioritize speed and stability over features.

Watcher may change frequently, so we strongly suggest you subscribe to the subreddit [/r/watcher](https://www.reddit.com/r/watcher/) to stay informed of any announcements, feature discussion, or events that require user interaction.

Refer to the [wiki](https://github.com/nosmokingbandit/Watcher3/wiki) for more information about post-processing, start scripts, and other features.

## Installation

Watcher requires [Python 3](https://www.python.org/).

It is also strongly recommended that you install [GIT](http://git-scm.com/). This will allow you to update much more easily.

**Download the required files using GIT:**

If you choose to use Git follow these steps.

* Open a terminal and cd to the directory you in which you want to install Watcher.
* Run `git clone https://github.com/nosmokingbandit/Watcher3.git`
* Start Watcher using `python3 watcher/watcher.py`
* Open a browser and navigate to `localhost:9090`

**Download ZIP:**

If you do not wish to use Git, follow these steps.

* Open your browser and go to `https://github.com/nosmokingbandit/Watcher3`
* Click on the green `Clone or download` button and click `Download ZIP`
* Once done downloading, extract the ZIP to the location in which you want Watcher installed
* Open a terminal and cd to the Watcher directory.
* Start Watcher using `python3 watcher/watcher.py`
* Open a browser and navigate to `localhost:9090`


## Usage

You can add the following arguments to Watcher when running the Python script.
Always use the absolute path when supplying a directory or file argument.

Run the server as a daemon (*nix only)

`$ watcher.py --daemon`

Run the server as a background process (Windows only)

`$ pythonw watcher.py --daemon`

Change address to bind to.

`$ watcher.py --address 0.0.0.0`

Change port to host on.

`$ watcher.py --port 9090`

Open browser on launch.

`$ watcher.py --browser`

Change path to config file. If not present, one will be created.

`$ watcher.py --conf /path/to/config.cfg`

Change path of log directory.

`$ watcher.py --log /path/to/logs/`

Change path to database. If not present, a new, empty database will be created.

`$ watcher.py --db /path/to/database.sqlite`

Change path to plugins directory.

`$ watcher.py --plugins /path/to/plugins/`

Create PID file.

`$ watcher.py --pid /path/to/pid/file.pid`

## Backup / Restore

Watcher includes a simple script for backing up and restoring your database and config.

The backup function will create a new watcher.zip in the Watcher folder.

To restore, place watcher.zip in the Watcher folder of your target installation and run the restore command.

#### Usage
Back up Watcher.

`$ backup.py -b`

Restore Watcher.

`$ backup.py -r`

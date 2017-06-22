import logging
from datetime import datetime, timedelta
from threading import Timer
import os
import json
from cherrypy.process import plugins

logging = logging.getLogger(__name__)


class SchedulerPlugin(plugins.SimplePlugin):
    '''
    CherryPy plugin that schedules events at a specific time of day,
        repeating at a certain interval.

    __init__
    bus: class instance of Cherrypy engine

    Class Vars:
    task_list: list of ScheduledTask instances.

    Requires that each ScheduledTask instance be appended to task_list

    On stop, terminates Timer for each task in task_list

    '''

    task_list = {}

    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)

    def start(self):
        return

    def stop(self):
        for name, task in self.task_list.items():
            task.stop()


class ScheduledTask(object):
    ''' Class that creates a new scheduled task.
    Creates a controller for class 'Task' with methods to
        start, stop, and reload.


    __init__:
    hour: int hour to first execute function (24hr time)
    minute: int minute to first execute function
    interval: int how many *seconds* to wait between executions
    task: function reference to function to execute
    auto_start: bool If timer should start on creation <default True>

    Creates a persistence_file that records the last execution of the
        scheduled task. This file is updated immediately before executing
        'task' and records the current time.


    Executes a given 'task' function on a scheduled basis.
    First execution occurs at hr:min
    Subsequent executions occur at regularly afterwards, at
        intervals of 'interval' seconds

    'task' will always run in a separate thread.

    Class Methods:
        start()     Starts countdown to initial execution
        stop()      Stops countdown. Waits for any in-process tasks to finish
        reload()    Calls stop(), __init__(), then start(), takes same args as create()

    Class Vars: (there are more, but interact with them at your own risk)
        name: str name of 'function'
        delay: int seconds to next execution

    Does not return
    '''

    persistence_file = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'tasks.json')
    persistence_record = None
    f = None

    def __init__(self, hour, minute, interval, task, auto_start=True):
        self.task = task
        self.task_name = task.__name__
        self.interval = interval

        if not ScheduledTask.f:
            ScheduledTask.f = open(self.persistence_file, 'w+')

        if not ScheduledTask.persistence_record:
            try:
                self.f.seek(0)
                ScheduledTask.persistence_record = json.load(self.f)
            except Exception as e:
                ScheduledTask.persistence_record = {}
                self.f.seek(0)
                json.dump({}, self.f)
                self.f.flush()

        record = ScheduledTask.persistence_record.get(self.task_name, {}).get('lastexecution', None)

        if record:
            next_exec = datetime.strptime(record, '%Y-%m-%d %H:%M:%S')
            hour, minute = next_exec.hour, next_exec.minute

        self.delay = self._calc_delay(hour, minute, interval)

        self.timer = Timer(self.delay, self._task)

        if auto_start:
            self.start()

        SchedulerPlugin.task_list[self.task_name] = self

    def _calc_delay(self, hour, minute, interval):
        ''' Calculates the next possible time to run an iteration
        hour: int hour of day (24hr time)
        minute: int minute of hour
        interval: int seconds between iterations

        Hour and minute represent a time of day that and interval will take place.
            This time can be in the future or past.

        Calculates the shortest delay from now that the interval can happen.
        If the difference between now and the delay is 0, the delay is equal to the interval.abs

        If minutes is greater than 60 it will be rolled over into hours.

        Returns int seconds until next interval

        '''
        rollover_hrs = 0
        while minute >= 60:
            minute -= 60
            rollover_hrs += 1

        rollover = timedelta(hours=rollover_hrs)

        now = datetime.today().replace(second=0, microsecond=0)
        next = now.replace(hour=hour, minute=minute) + rollover

        while next < now:
            next += timedelta(seconds=interval)

        delay = (next - now).seconds
        # this prevents infinite loops if the task restarts the plugin
        if delay == 0:
            delay = interval

        return delay

    def _task(self):
        self.timer = Timer(self.interval, self._task)
        self.timer.start()
        # Set record
        self.f.seek(0)
        p = json.load(self.f)
        p[self.task_name] = {'lastexecution': str(datetime.today().replace(second=0, microsecond=0))}
        self.f.seek(0)
        json.dump(p, self.f)
        self.f.flush()

        self.task()

    def start(self):
        self.timer.start()

    def stop(self):
        if self.timer.is_alive():
            logging.info('Stopping scheduled task {}.'.format(self.task_name))
            print('Stopping scheduled task: {}'.format(self.task_name))
            self.timer.cancel()

    def reload(self, hr, min, interval, auto_start=True):
        ''' Reloads scheduled task to change time or interval
        See self.__init__ for param descriptions
        '''

        logging.info('Reloading scheduler for {}'.format(self.task_name))
        try:
            self.timer.cancel()
            self.__init__(hr, min, interval, self.task, auto_start=auto_start)
            return True
        except Exception as e:
            logging.error('Unable to start task', exc_info=True)
            return e
import logging
from datetime import datetime, timedelta
from threading import Timer

from cherrypy.process import plugins

logging = logging.getLogger(__name__)


class SchedulerPlugin(plugins.SimplePlugin):
    '''
    CherryPy plugin that schedules events at a specific time of day,
        repeating at a certain interval.

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
    __init__
    :param hr: int hour to first execute function (24hr time)
    :param min: int minute to first execute function
    :param interval: int how many *seconds* to wait between executions
    :param task: function reference to function to execute
    :param auto_start: bool If timer should start on creation <default True>


    Executes a given 'task' function on a scheduled basis.
    First execution occurs at hr:min
    Subsequent executions occur at regularly afterwards, at
        intervals of 'interval' seconds

    Class Methods:
        start()     Starts countdown to initial execution
        stop()      Stops countdown. Waits for any in-process tasks to finish
        reload()    Calls stop(), __init__(), then start(), takes same args as create()

    Does not return
    '''

    def __init__(self, hr, min, interval, task, auto_start=True):
        self.name = task.__name__
        self.task_fn = task

        self.task = Task(hr, min, interval, task)

        if auto_start is True:
            self.start()

        SchedulerPlugin.task_list[self.name] = self

    def start(self):
        self.task.timer.start()

    def stop(self):
        logging.info('Stopping scheduled task {}.'.format(self.name))
        print('Stopping scheduled task: {}'.format(self.name))
        self.task.timer.cancel()

    def reload(self, hr, min, interval, auto_start=True):
        ''' Reloads scheduled task to change time or interval
        See self.__init__ for param descriptions
        '''

        logging.info('Reloading scheduler for {}'.format(self.name))
        try:
            self.task.timer.cancel()
            self.__init__(hr, min, interval, self.task_fn, auto_start=auto_start)
            return True
        except Exception as e:
            logging.error('Unable to start task', exc_info=True)
            return e


class Task(object):
    def __init__(self, hour, minute, interval, func):
        self.interval = interval
        self.func = func

        rollover_hrs = 0
        while minute >= 60:
            minute -= 60
            rollover_hrs += 1

        rollover = timedelta(hours=rollover_hrs)

        now = datetime.today().replace(second=0, microsecond=0)
        next = now.replace(hour=hour, minute=minute) + rollover

        while next < now:
            next += timedelta(seconds=self.interval)

        self.delay = (next - now).seconds
        # this prevents infinite loops if the task restarts the plugin
        if self.delay == 0:
            self.delay = self.interval

        self.timer = Timer(self.delay, self.task)

    def task(self):
        self.timer = Timer(self.interval, self.task)
        self.timer.start()
        self.func()


''' Global commands.

cherrypy.engine.scheduler.{taskname}.stop()
                                    .restart()
                                    .start()
Restart entire engine:
cherrypy.engine.graceful()


To add new task:

Create new class, inherit Manager
In __init__
    Gather time of day to start, interval, and function to fire.
    Pass to scheduler like this:
        self.named_task = Task(hr, min, interval, self.searcher.auto_search)

In class ScheduledTasks, add to start, stop, and restart.
I'll eventually make a list of tasks and have start/stop/resart iterate over.
But that is a job for tomorrow.

'''

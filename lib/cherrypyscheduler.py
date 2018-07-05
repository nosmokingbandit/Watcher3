import logging
from datetime import datetime, timedelta
from threading import Timer, Lock
import os
import json
from cherrypy.process import plugins

logging = logging.getLogger('CPTaskScheduler')


class _Record(object):
    ''' Default tasks record handler
    Will read/write from/to ./tasks.json
    '''
    lock = Lock()
    file = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'tasks.json')

    @staticmethod
    def read():
        ''' Reads persistence record to dict

        Returns dict
        '''

        with _Record.lock:
            with open(_Record.file, 'a+') as f:
                try:
                    f.seek(0)
                    r = json.load(f)
                except Exception as _: # noqa
                    r = {}
                    json.dump(r, f)
        return r

    @staticmethod
    def write(name, le):
        ''' Writes record to record_handler
        name (str): name of task
        le (str): str() cast of datetime.datetime object for last execution

        Does not return
        '''
        with _Record.lock:
            with open(_Record.file, 'r+') as f:
                r = json.load(f)
                r[name] = {'last_execution': le}
                f.seek(0)
                json.dump(r, f, indent=4, sort_keys=True)
                f.seek(0)


class SchedulerPlugin(plugins.SimplePlugin):
    '''
    CherryPy plugin that schedules events at a specific time of day,
        repeating at a certain interval.


    Class Methods:
        __init__
            bus (obj): instance of Cherrypy engine

    Class Vars:
        task_list (dict): {'task_name': <instance of ScheduledTask>}.
        record (dict): {'task_name': {'last_execution': '2017-01-01 23:28:00'}}
        record_handler (class): class with staticmethods read() and write(); see _Record

    Requires that each ScheduledTask instance be appended to task_list

    On stop, terminates Timer for each task in task_list
    '''

    task_list = {}
    record = None
    record_handler = _Record

    def __init__(self, bus, record_handler=_Record, record_file=None):
        '''
        bus (obj): instance of cherrypy.engine
        record_handler (object): class to handle read/write of record data  <optional, default _Record>
        record_file (str): path to task record file. Only effective with default record_handler. <default './tasks.json'>

        record_handler MUST be a class with staticmethods of 'read' and 'write'.
            See _Record class for method descriptions and requirements.

        If record_file is not specified writes to this script's directory as 'tasks.json'
        '''
        _Record.file = record_file or _Record.file
        plugins.SimplePlugin.__init__(self, bus)
        SchedulerPlugin.record_handler = record_handler or SchedulerPlugin.record_handler
        SchedulerPlugin.record = record_handler.read()

    def start(self):
        for t in self.task_list.values():
            if t.auto_start:
                t.start()
        return
    start.priority = 75

    def stop(self):
        ''' Calls task.stop for all tasks in task_list '''
        for name, task in self.task_list.items():
            task.stop()

    def restart(self):
        ''' Calls task.restart for all tasks in task_list '''
        for name, task in self.task_list.items():
            task.restart()

    @staticmethod
    def ScheduledTask(hour, minute, interval, task, auto_start=True, name=None):
        ''' Creates and returns instance of __ScheduledTask '''

        return SchedulerPlugin.__ScheduledTask(hour, minute, interval, task, auto_start, name)

    class __ScheduledTask(object):
        ''' Class that creates a new scheduled task.

        __init__:
            hour (int): hour to first execute function (24hr time)
            minute (int): minute to first execute function
            interval (int): how many *seconds* to wait between executions
            task (function): function to execute on timer
            auto_start (bool): if timer should start on creation    <optional - default True>
            name (str): name of sceduled task                       <optional - default None>

        Creates a persistence_file that records the last execution of the
            scheduled task. This file is updated immediately before executing
            'task' and records the current time.

            If a task does not have a persistence record, adds one using current
            time. This ensures that long-interval tasks are not perpetually
            delayed if the server updates or restarts often.

            Stores persistence record in SchedulerPlugin.record as dict

        Executes a given 'task' function on a scheduled basis
        First execution occurs at hr:min
        Subsequent executions occur at regularly afterwards, at
            intervals of 'interval' seconds

        'task' will always run in a separate thread

        Class Methods:
            start()     Starts countdown to initial execution
            stop()      Stops countdown. Allows any in-process tasks to finish
            reload()    Cancels timer then calls __init__() and start(), takes same args as
                            __init__ and just passes them along to __init__
            now()       Bypasses timer and executes function now. Starts a new timer
                            based off the current time

        Class Vars: (there are more, but interact with them at your own risk)
            name (str): passed arg 'name' or name of 'task' function if not passed
            interval (int): interval between executions
            running (bool): if assigned task is currently being executed
            last_execution (str): timestamp of last execution formatted as '%Y-%m-%d %H:%M:%S' ('2017-07-23 17:31:40')
            next_execution (obj): datetime.datetime obj of next execution

        Does not return
        '''

        def __init__(self, hour, minute, interval, task, auto_start, name):
            self._init_args = [hour, minute, interval, task, auto_start, name]
            self.task = task
            self.name = name or task.__name__
            self.interval = interval
            self.running = False
            self.auto_start = auto_start
            self.timer = Timer(0, None)
            self.next_execution = None

            record = SchedulerPlugin.record.get(self.name, {}).get('last_execution')

            if record:
                self.last_execution = record
                le = datetime.strptime(record, '%Y-%m-%d %H:%M:%S')
                hour, minute = le.hour, le.minute
            else:
                le = datetime.today().replace(microsecond=0)
                self.last_execution = str(le)
                SchedulerPlugin.record_handler.write(self.name, str(le))

            SchedulerPlugin.task_list[self.name] = self

        def _calc_delay(self, hour, minute, interval):
            ''' Calculates the next possible time to run an iteration based off
                last_execution as decribed in the record_handler
            hour (int): hour of day (24hr time)
            minute (int): minute of hour
            interval (int): seconds between iterations

            Hour and minute represent a time of day that and interval will begin.
                This time can be in the future or past.

            Calculates the shortest delay from now that the interval can happen.
            If the difference between now and the delay is 0, the delay is
                equal to the interval and will not execute immediately.

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

            while delay > interval:
                delay -= interval

            # this prevents infinite loops if the task restarts the plugin
            if delay == 0:
                delay = interval

            return delay

        def _task(self, manual=False, restart=True):
            ''' Executes the task fn
            manual (bool): if task is being ran by user command     <optional - default False>
            restart (bool): if the timer should be restarted        <optional - default True>
            manual flag only affects logging

            Starts new timer based on self.interval
            Gets current time as 'le'
            Sets self.running to True, runs task, sets as False

            After task is finished, le is written to record. This way tasks can have
                access to their last execution time while running.

            Does not return
            '''

            now = datetime.today()
            ms_offset = now.microsecond / 1000000
            now = now.replace(microsecond=0)

            if manual:
                logging.info('== Executing Task: {} Per User Command =='.format(self.name))
            else:
                logging.info('== Executing Scheduled Task: {} =='.format(self.name))

            if self.running:
                logging.warning('Task {} is already running, cancelling execution.')
                return

            self.running = True

            if restart:
                self.next_execution = now.replace(microsecond=0) + timedelta(seconds=self.interval)
                self.timer = Timer(self.interval - ms_offset, self._task)
                self.timer.start()

            try:
                self.task()
            except Exception as _:  # noqa
                logging.warning('Scheduled Task {} Failed:'.format(self.name), exc_info=True)
            self.running = False
            self.last_execution = str(now)
            SchedulerPlugin.record[self.name] = {'last_execution': str(now)}
            SchedulerPlugin.record_handler.write(self.name, str(now))

            if manual:
                logging.info('== Finished Task: {} =='.format(self.name))
            else:
                logging.info('== Finished Scheduled Task: {} =='.format(self.name))

        def start(self):
            ''' Starts timer Thread for task '''
            delay = self._calc_delay(*self._init_args[:3])
            self.next_execution = datetime.now().replace(microsecond=0) + timedelta(seconds=delay)
            self.timer = Timer(delay, self._task)
            self.timer.start()

        def stop(self):
            ''' Stops Timer if currently running

            Logs and prints task name being cancelled
            Cancels timer for next task
            Will not stop a task currently being executed

            Allows in-process tasks to finish, will not kill thread.
            '''

            if self.timer and self.timer.is_alive():
                logging.info('Stopping scheduled task {}.'.format(self.name))
                print('Stopping scheduled task: {}'.format(self.name))
                self.timer.cancel()

        def reload(self, hr, min, interval, auto_start=True):
            ''' Reloads scheduled task to change time or interval
            See self.__init__ for param descriptions.

            Does not require 'task', or 'name' args since that is
                stored in the class instance as self.task & self.name

            Stops current timer (allowing in-process tasks to finish, same as self.stop())
            Calls self.__init__ with passed args.
            Starts timer.

            Use to change start time or interval.

            Returns bool
            '''

            logging.info('Reloading scheduler for {}'.format(self.name))
            self.stop()
            try:
                self.__init__(hr, min, interval, self.task, auto_start=auto_start, name=self.name)
                if auto_start:
                    self.start()
                return True
            except Exception as _:  # noqa
                logging.error('Unable to start task', exc_info=True)
                return False

        def restart(self):
            ''' Restarts stopped task using initial parameters

            Unlike self.reload(), does not change any timing information.

            Calls self.stop() to ensure timer is stopped before restarting.

            Uses self._init_args to start timer based on original params.

            Does not return
            '''

            logging.info('Restarting schduled task {}'.format(self.name))
            self.stop()

            self.__init__(*self._init_args)
            if self.auto_start:
                self.start()

        def now(self):
            ''' Skips Thread timer and executes task now

            If _task isn't being executed currently, stops timer and runs task.
            Will restart timer if it was running when now() was called. New timer
                will start from the current time

            Raises TimerConflictError if task is alread running

            Returns str last execution timestamp
            '''

            if self.running:
                raise TimerConflictError('The task {} is currently being executed.'.format(self.name))
            else:
                restart = False
                if self.timer:
                    self.timer.cancel()
                    restart = self.timer.is_alive()
                self._task(manual=True, restart=restart)
            return self.last_execution


class TimerConflictError(Exception):
    ''' Raised when a timed task is in conflict with itself '''
    def __init__(self, msg=None):
        self.msg = msg if msg else 'An error occured with the timer for a scheduled task.'

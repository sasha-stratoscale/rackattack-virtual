import threading
import collections
import time
from rackattack.common import globallock
from rackattack.tcp import suicide
import logging


def scheduleIn(**kwargs):
    TimersThread.it.scheduleIn(**kwargs)


def scheduleAt(**kwargs):
    TimersThread.it.scheduleAt(**kwargs)


def cancelAllByTag(**kwargs):
    TimersThread.it.cancelAllByTag(**kwargs)


_Timer = collections.namedtuple('_Timer', ['when', 'callback', 'tag'])


class TimersThread(threading.Thread):
    it = None

    def __init__(self):
        self._timers = []
        self._event = threading.Event()
        TimersThread.it = self
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def scheduleIn(self, timeout, callback, tag):
        self.scheduleAt(when=time.time() + timeout, callback=callback, tag=tag)

    def scheduleAt(self, when, callback, tag):
        assert globallock.assertLocked()
        self._timers.append(_Timer(when=when, callback=callback, tag=tag))
        self._timers.sort(key=lambda x: x.when)
        self._event.set()

    def cancelAllByTag(self, tag):
        assert globallock.assertLocked()
        self._timers = [t for t in self._timers if t.tag is not tag]
        self._event.set()

    def run(self):
        try:
            timeout = None
            while True:
                self._event.wait(timeout=timeout)
                self._event.clear()
                with globallock.lock:
                    self._runOne()
                    timeout = self._nextTimeout()
        except:
            logging.exception("Timers thread died")
            suicide.killSelf()
            raise

    def _nextTimeout(self):
        assert globallock.assertLocked()
        if len(self._timers) == 0:
            return None
        timeout = self._timers[0].when - time.time()
        if timeout < 0:
            timeout = 0
        return timeout

    def _runOne(self):
        assert globallock.assertLocked()
        if len(self._timers) == 0:
            return
        if self._timers[0].when > time.time():
            return
        timer = self._timers.pop(0)
        try:
            timer.callback()
        except:
            logging.exception("Timer '%(callback)s' raised", dict(callback=timer.callback))

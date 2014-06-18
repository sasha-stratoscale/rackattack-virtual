from rackattack.common import globallock
from rackattack.common import timer
import collections
import time
import logging


_Host = collections.namedtuple('_Host', ['stateMachine', 'freedAt'])


class FreePool:
    _FREE_IF_UNUSED_FOR = 5 * 60

    def __init__(self, hosts):
        self._hosts = hosts
        self._pool = []
        self._putListeners = []

    def put(self, hostStateMachine):
        assert globallock.assertLocked()
        self._pool.append(_Host(hostStateMachine, time.time()))
        hostStateMachine.setDestroyCallback(self._hostSelfDestructed)
        self._rescheduleTimer()
        for listener in self._putListeners:
            listener()

    def all(self):
        assert globallock.assertLocked()
        for host in self._pool:
            yield host.stateMachine

    def takeOut(self, hostStateMachine):
        assert globallock.assertLocked()
        for host in self._pool:
            if host.stateMachine is hostStateMachine:
                self._pool.remove(host)
                hostStateMachine.setDestroyCallback(None)
                return
        raise AssertionError("HostStateMachine not in free pool")

    def registerPutListener(self, callback):
        assert callback not in self._putListeners
        self._putListeners.append(callback)

    def unregisterPutListener(self, callback):
        assert callback in self._putListeners
        self._putListeners.remove(callback)

    def _rescheduleTimer(self):
        self._pool.sort(key=lambda x: x.freedAt)
        timer.cancelAllByTag(tag=self)
        if len(self._pool) > 0:
            when = self._pool[0].freedAt + self._FREE_IF_UNUSED_FOR
            timer.scheduleAt(when=when, callback=self._destroyUnused, tag=self)

    def _destroyUnused(self):
        assert globallock.assertLocked()
        timeout = time.time() - self._FREE_IF_UNUSED_FOR
        while len(self._pool) > 0 and self._pool[0].freedAt < timeout:
            host = self._pool.pop(0)
            logging.info("VM %(index)d unused for a while, destroying", dict(
                index=host.stateMachine.hostImplementation().index()))
            self._hosts.destroy(host.stateMachine)

    def _hostSelfDestructed(self, hostStateMachine):
        assert globallock.assertLocked()
        self._hosts.destroy(hostStateMachine)
        for host in self._pool:
            if host.stateMachine is hostStateMachine:
                self._pool.remove(host)
                return
        raise AssertionError("HostStateMachine not in free pool")

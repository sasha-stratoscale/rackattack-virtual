from rackattack.common import globallock
from rackattack.tcp import debug
from inaugurator.server import server
import logging


class Inaugurate:
    def __init__(self, bindHostname):
        self._registered = {}
        self._server = server.Server(
            bindHostname=bindHostname, checkInCallback=self._checkIn, doneCallback=self._done)

    def register(self, ipAddress, checkInCallback, doneCallback):
        assert globallock.assertLocked()
        assert ipAddress not in self._registered
        self._registered[ipAddress] = dict(checkInCallback=checkInCallback, doneCallback=doneCallback)

    def unregister(self, ipAddress):
        assert globallock.assertLocked()
        assert ipAddress in self._registered
        del self._registered[ipAddress]

    def provideLabel(self, ipAddress, label):
        logging.info("%(ipAddress)s received label '%(label)s'", dict(
            ipAddress=ipAddress, label=label))
        with debug.logNetwork("Providing label '%(label)s' to '%(ipAddress)s'" % dict(
                label=label, ipAddress=ipAddress)):
            self._server.provideLabel(ipAddress=ipAddress, label=label)

    def _checkIn(self, ipAddress):
        logging.info("%(ipAddress)s check in", dict(ipAddress=ipAddress))
        with globallock.lock():
            if ipAddress not in self._registered:
                logging.error("Unknown Inaugurator checked in: %(ipAddress)s", dict(ipAddress=ipAddress))
                return
            self._registered[ipAddress]['checkInCallback']()

    def _done(self, ipAddress):
        logging.info("%(ipAddress)s done", dict(ipAddress=ipAddress))
        with globallock.lock():
            if ipAddress not in self._registered:
                logging.error("Unknown Inaugurator checked in: %(ipAddress)s", dict(ipAddress=ipAddress))
                return
            self._registered[ipAddress]['doneCallback']()

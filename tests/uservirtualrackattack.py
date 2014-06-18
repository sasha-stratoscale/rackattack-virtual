import subprocess
import os
import shutil
import time
from rackattack import clientfactory
from tests import testlib
import rackattack


class UserVirtualRackAttack:
    MAXIMUM_VMS = 4

    def __init__(self):
        assert '/usr' not in rackattack.__file__
        self._requestPort = 3443
        self._subscribePort = 3444
        imageDir = os.path.join(os.getcwd(), "images.fortests")
        shutil.rmtree(imageDir, ignore_errors=True)
        self._popen = subprocess.Popen(
            ["sudo", "PYTHONPATH=.", "UPSETO_JOIN_PYTHON_NAMESPACES=Yes",
                "python", "rackattack/virtual/main.py",
                "--requestPort=%d" % self._requestPort,
                "--subscribePort=%d" % self._subscribePort,
                "--diskImagesDirectory=" + imageDir,
                "--serialLogsDirectory=" + imageDir,
                "--maximumVMs=%d" % self.MAXIMUM_VMS],
            close_fds=True, stderr=subprocess.STDOUT)
        testlib.waitForTCPServer(('localhost', self._requestPort))
        time.sleep(0.5)  # dnsmasq needs to be able to receive a SIGHUP

    def done(self):
        if self._popen.poll() is not None:
            raise Exception("Virtual RackAttack server terminated before it's time")
        subprocess.check_call(["sudo", "kill", str(self._popen.pid)], close_fds=True)
        self._popen.wait()

    def createClient(self):
        os.environ['RACKATTACK_PROVIDER'] = 'tcp://localhost:%d@tcp://localhost:%d' % (
            self._requestPort, self._subscribePort)
        return clientfactory.factory()

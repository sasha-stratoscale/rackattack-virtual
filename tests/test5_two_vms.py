import unittest
from tests import uservirtualrackattack
from tests import testlib
import rackattack
from rackattack.ssh import connection
connection.discardParamikoLogs()
connection.discardSSHDebugMessages()


class Test(unittest.TestCase):
    def setUp(self):
        self.assertTrue('/usr/' not in rackattack.__file__)
        self.server = uservirtualrackattack.UserVirtualRackAttack()

    def tearDown(self):
        self.server.done()

    def test_it(self):
        self.client = self.server.createClient()
        self.assertEquals(self.server.MAXIMUM_VMS, 4)
        allocation = self.client.allocate(
            requirements={
                'node1': testlib.defaultRequirement(),
                'node2': testlib.defaultRequirement()},
            allocationInfo=testlib.whiteboxAllocationInfo())
        allocation.wait(timeout=8 * 60)
        self.assertFalse(allocation.dead())
        self.assertTrue(allocation.done())
        nodes = allocation.nodes()
        node1 = nodes['node1']
        ssh1 = connection.Connection(**node1.rootSSHCredentials())
        ssh1.waitForTCPServer()
        ssh1.connect()
        self.assertEquals(ssh1.run.script("echo hello"), "hello")
        node2 = nodes['node2']
        ssh2 = connection.Connection(**node2.rootSSHCredentials())
        ssh2.waitForTCPServer()
        ssh2.connect()
        self.assertEquals(ssh2.run.script("echo hello"), "hello")
        allocation.free()


if __name__ == '__main__':
    unittest.main()

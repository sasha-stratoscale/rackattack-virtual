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
            requirements={'node': testlib.defaultRequirement()},
            allocationInfo=testlib.whiteboxAllocationInfo())
        allocation.wait(timeout=5 * 60)
        self.assertFalse(allocation.dead())
        self.assertTrue(allocation.done())
        nodes = allocation.nodes()
        self.assertEquals(len(nodes), 1)
        node = nodes['node']
        ssh = connection.Connection(**node.rootSSHCredentials())
        ssh.waitForTCPServer()
        ssh.connect()
        result = ssh.run.script("echo hello")
        self.assertEquals(result.strip(), "hello")
        allocation.free()


if __name__ == '__main__':
    unittest.main()

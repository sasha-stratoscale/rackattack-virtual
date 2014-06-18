import unittest
from tests import uservirtualrackattack
from tests import testlib
import rackattack
import time


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
        time.sleep(1)
        self.assertFalse(allocation.dead())
        self.assertFalse(allocation.done())
        allocation.free()


if __name__ == '__main__':
    unittest.main()

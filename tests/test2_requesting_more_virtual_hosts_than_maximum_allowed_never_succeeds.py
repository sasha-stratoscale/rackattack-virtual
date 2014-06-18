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
            requirements={'node%d' % i: testlib.defaultRequirement()
                for i in xrange(1, self.server.MAXIMUM_VMS + 2)},
            allocationInfo=testlib.whiteboxAllocationInfo())
        before = time.time()
        try:
            allocation.wait(timeout=3)
        except Exception as e:
            self.assertIn('large allocation', str(e).lower())
        else:
            self.assertTrue(False, "allocation should have failed")
        self.assertLess(time.time() - before, 2)
        self.assertIn('large allocation', allocation.dead().lower())


if __name__ == '__main__':
    unittest.main()

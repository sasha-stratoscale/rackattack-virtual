import unittest
from tests import uservirtualrackattack
import rackattack


class Test(unittest.TestCase):
    def setUp(self):
        self.assertTrue('/usr/' not in rackattack.__file__)
        self.server = uservirtualrackattack.UserVirtualRackAttack()

    def tearDown(self):
        self.server.done()

    def test_emptyConnection(self):
        self.server.createClient()

if __name__ == '__main__':
    unittest.main()

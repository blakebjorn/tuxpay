# some unit tests are modifying globals...
import shutil
import tempfile
import threading
import unittest

from modules.electrum_mods.functions import constants


class SequentialTestCase(unittest.TestCase):

    test_lock = threading.Lock()

    def setUp(self):
        super().setUp()
        self.test_lock.acquire()

    def tearDown(self):
        super().tearDown()
        self.test_lock.release()


class ElectrumTestCase(SequentialTestCase):
    """Base class for our unit tests."""

    def setUp(self):
        super().setUpClass()
        self.electrum_path = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDownClass()
        shutil.rmtree(self.electrum_path)


class TestCaseForTestnet(ElectrumTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constants.set_testnet()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        constants.set_mainnet()
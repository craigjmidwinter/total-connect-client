# test total_connect_client

import unittest

#from total_connect_client import TotalConnectClient
import TotalConnectClient

PASSWORD_BAD = 'none'
USERNAME_BAD = 'none'

class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def tests_bad_credentials(self):
        with self.assertRaises(TotalConnectClient.AuthenticationError):
            client = TotalConnectClient.TotalConnectClient(USERNAME_BAD, PASSWORD_BAD)


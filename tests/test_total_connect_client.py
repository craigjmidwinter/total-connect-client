# test total_connect_client

import unittest
from unittest.mock import Mock, patch

#from total_connect_client import TotalConnectClient
import TotalConnectClient

PASSWORD_BAD = 'none'
USERNAME_BAD = 'none'

class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        pass

    def tearDown(self):
        self.client = None

    def tests_bad_credentials(self):
        with self.assertRaises(TotalConnectClient.AuthenticationError):
            badclient = TotalConnectClient.TotalConnectClient(USERNAME_BAD, PASSWORD_BAD)


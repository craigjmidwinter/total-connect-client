"""Test total_connect_client."""

import unittest

import TotalConnectClient

PASSWORD_BAD = "none"
USERNAME_BAD = "none"


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        pass

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_bad_credentials(self):
        """Test bad credentials."""

        with self.assertRaises(TotalConnectClient.AuthenticationError):
            badclient = TotalConnectClient.TotalConnectClient(
                USERNAME_BAD, PASSWORD_BAD
            )
            
            self.assertFalse(badclient.valid_credentials)
            self.assertFalse(badclient.is_logged_in())
            self.assertTrue(badclient.log_out())
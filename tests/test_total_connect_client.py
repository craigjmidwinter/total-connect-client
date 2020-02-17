"""Test total_connect_client."""

import unittest

import TotalConnectClient

PASSWORD_BAD = "none"
USERNAME_BAD = "none"


class FakeGoodClient(TotalConnectClient.TotalConnectClient):
    """Fake total connect client."""

    def authenticate(self):
        """Pretend to authenticate."""
        self.token = True
        self.valid_credentials = True


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = FakeGoodClient(USERNAME_BAD, PASSWORD_BAD)

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

    def tests_good_client(self):
        """Tests a good client."""
        self.assertTrue(self.client.valid_credentials)
        self.assertTrue(self.client.is_logged_in())

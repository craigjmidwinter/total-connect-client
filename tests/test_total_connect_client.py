"""Test total_connect_client."""

import unittest

import TotalConnectClient

from const import PASSWORD_BAD, USERNAME_BAD


class FakeGoodClient(TotalConnectClient.TotalConnectClient):
    """Fake total connect client."""

    def authenticate(self):
        """Pretend to authenticate."""
        self.token = True
        self._valid_credentials = True

    def logout(self):
        """Pretend to logout."""
        if self.is_logged_in():
            self.token = False
            return True

        return False


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = FakeGoodClient(USERNAME_BAD, PASSWORD_BAD)
        self.badclient = TotalConnectClient.TotalConnectClient(
            USERNAME_BAD, PASSWORD_BAD
        )

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_bad_credentials(self):
        """Test bad credentials."""
        self.assertFalse(self.badclient.is_valid_credentials())
        self.assertFalse(self.badclient.is_logged_in())
        self.assertFalse(self.badclient.log_out())

    def tests_good_client(self):
        """Tests a good client."""
        self.assertTrue(self.client.is_valid_credentials())
        self.assertTrue(self.client.is_logged_in())
        self.assertTrue(self.client.logout())
        self.assertFalse(self.client.is_logged_in())

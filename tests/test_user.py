"""Test total_connect_user."""

import unittest

from TotalConnectClient import total_connect_user

USER_GOOD = {
    "UserID": "1234567",
    "Username": "username",
    "UserFeatureList": "Master=0,User Administration=0,Configuration Administration=0",
}

USER_BAD_MASTER = {
    "UserID": "1234567",
    "Username": "username",
    "UserFeatureList": "Master=1,User Administration=0,Configuration Administration=0",
}

USER_BAD_CONFIG = {
    "UserID": "1234567",
    "Username": "username",
    "UserFeatureList": "Master=0,User Administration=1,Configuration Administration=1",
}


class TestUser(unittest.TestCase):
    """Test total_connect_user."""

    def setUp(self):
        """Test setup."""
        self.user_good = total_connect_user(USER_GOOD)
        self.user_bad_master = total_connect_user(USER_BAD_MASTER)
        self.user_bad_config = total_connect_user(USER_BAD_CONFIG)

    def tearDown(self):
        """Tear down."""
        self.user_good = None
        self.user_bad_master = None
        self.user_bad_config = None

    def tests_security(self):
        """Test security_check()."""
        self.assertFalse(self.user_good.security_problem())
        self.assertTrue(self.user_bad_master.security_problem())
        self.assertTrue(self.user_bad_config.security_problem())

"""Total Connect User."""

import logging

LOGGER = logging.getLogger(__name__)


class TotalConnectUser:
    """User for Total Connect."""

    def __init__(self, user_info):
        """Initialize based on UserInfo from LoginAndGetSessionDetails."""
        self._user_id = user_info["UserID"]
        self._username = user_info["Username"]
        self._features = dict(
            x.split("=") for x in user_info["UserFeatureList"].split(",")
        )
        self._master_user = self._features["Master"] == "1"
        self._user_admin = self._features["User Administration"] == "1"
        self._config_admin = self._features["Configuration Administration"] == "1"

        if self.security_problem():
            LOGGER.warning(
                f"Total Connect user {self._username} has one or "
                "more permissions that are not necessary. Remove "
                "permissions from this user or create a new user "
                "with minimal permissions."
            )

    def security_problem(self):
        """Run security checks. Return true if problem."""
        problem = False

        if self._master_user:
            LOGGER.warning(f"User {self._username} is a master user.")
            problem = True

        if self._user_admin:
            LOGGER.warning(f"User {self._username} is a user administrator.")
            problem = True

        if self._config_admin:
            LOGGER.warning(
                f"User {self._username} " "is a configuration administrator."
            )
            problem = True

        return problem

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"Username: {self._username}\n"
            f"UserID: {self._user_id}\n"
            f"Master User: {self._master_user}\n"
            f"User Administrator: {self._user_admin}\n"
            f"Configuration Administrator: {self._config_admin}\n"
            "User features:\n"
        )

        for key, value in self._features.items():
            data = data + f"  {key}: {value}\n"

        return data + "\n"

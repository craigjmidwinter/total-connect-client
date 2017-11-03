import zeep
import logging

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

class TotalConnectClient:
    DISARMED = 10200
    DISARMED_BYPASS = 10211
    ARMED_AWAY = 10201
    ARMED_AWAY_BYPASS = 10202
    ARMED_AWAY_INSTANT = 10205
    ARMED_AWAY_INSTANT_BYPASS = 10206
    ARMED_STAY = 10203
    ARMED_STAY_BYPASS = 10204
    ARMED_STAY_INSTANT = 10209
    ARMED_STAY_INSTANT_BYPASS = 10210
    ARMED_STAY_NIGHT = 10218
    ARMING = 10307
    DISARMING = 10308

    def __init__(self, username, password):
        self.soapClient = zeep.Client('https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL')

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.token = False

        self.locations = []

        self.authenticate()

    def authenticate(self):
        """Login to the system."""

        response = self.soapClient.service.AuthenticateUserLogin(self.username, self.password, self.applicationId, self.applicationVersion)
        if response.ResultData == 'Success':
            self.token = response.SessionID
            self.populate_details()
        else:
            Exception('Authentication Error')

    def populate_details(self):
        """Populates system details."""

        response = self.soapClient.service.GetSessionDetails(self.token, self.applicationId, self.applicationVersion)

        logging.info('Getting session details')

        self.locations = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']

        logging.info('Populated locations')

    def arm_away(self, location_name=False):
        """Arm the system (Away)."""

        self.arm(ARM_TYPE_AWAY, location_name)

    def arm_stay(self, location_name=False):
        """Arm the system (Stay)."""

        self.arm(ARM_TYPE_STAY, location_name)

    def arm_stay_instant(self, location_name=False):
        """Arm the system (Stay - Instant)."""

        self.arm(ARM_TYPE_STAY_INSTANT, location_name)

    def arm_away_instant(self, location_name=False):
        """Arm the system (Away - Instant)."""

        self.arm(ARM_TYPE_AWAY_INSTANT, location_name)

    def arm_stay_night(self, location_name=False):
        """Arm the system (Stay - Night)."""

        self.arm(ARM_TYPE_STAY_NIGHT, location_name)

    def arm(self, arm_type, location_name=False):
        """Arm the system."""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type, '-1')

        logging.info('armed')

    def get_security_panel_device_id(self, location):
        """Find the device id of the security panel."""
        deviceId = False
        for device in location['DeviceList']['DeviceInfoBasic']:
            if device['DeviceName'] == 'Security Panel' or device['DeviceName'] == 'Security System':
                deviceId = device['DeviceID']

        if deviceId is False:
            raise Exception('No security panel found')

        return deviceId

    def get_location_by_location_name(self, location_name=False):
        """Get the location object for a given name (or the default location if none is provided)."""

        location = False

        for loc in self.locations:
            if location_name is False and location is False:
                location = loc
            elif loc['LocationName'] == location_name:
                location = loc

        if location is False:
            raise Exception('Could not select location. Try using default location.')

        return location

    def get_armed_status(self, location_name=False):
        """Get the status of the panel."""
        location = self.get_location_by_location_name(location_name)

        response = self.soapClient.service.GetPanelMetaDataAndFullStatus(self.token, location['LocationID'], 0, 0, 1)

        status = zeep.helpers.serialize_object(response)

        alarm_code = status['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

        return alarm_code

    def is_armed(self, location_name=False):
        """Return True or False if the system is armed in any way"""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10201:
            return True
        elif alarm_code == 10202:
            return True
        elif alarm_code == 10205:
            return True
        elif alarm_code == 10206:
            return True
        elif alarm_code == 10203:
            return True
        elif alarm_code == 10204:
            return True
        elif alarm_code == 10209:
            return True
        elif alarm_code == 10210:
            return True
        elif alarm_code == 10218:
            return True
        else:
            return False

    def is_arming(self, location_name=False):
        """Return true or false is the system is in the process of arming."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10307:
            return True
        else:
            return False

    def is_disarming(self, location_name=False):
        """Return true or false is the system is in the process of disarming."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10308:
            return True
        else:
            return False

    def is_pending(self, location_name=False):
        """Return true or false is the system is pending an action."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10307 or alarm_code == 10308:
            return True
        else:
            return False

    def disarm(self, location_name=False):
        """Disarm the system."""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')

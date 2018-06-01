import zeep
import logging

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

class AuthenticationError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class TotalConnectClient:
    DISARMED = 10200
    DISARMED_BYPASS = 10211
    ARMED_AWAY = 10201
    ARMED_AWAY_BYPASS = 10202
    ARMED_AWAY_INSTANT = 10205
    ARMED_AWAY_INSTANT_BYPASS = 10206
    ARMED_CUSTOM_BYPASS = 10223
    ARMED_STAY = 10203
    ARMED_STAY_BYPASS = 10204
    ARMED_STAY_INSTANT = 10209
    ARMED_STAY_INSTANT_BYPASS = 10210
    ARMED_STAY_NIGHT = 10218
    ARMING = 10307
    DISARMING = 10308

    INVALID_SESSION = -102
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500

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

        response = self.soapClient.service.LoginAndGetSessionDetails(self.username, self.password, self.applicationId, self.applicationVersion)
        if response.ResultCode == self.SUCCESS:
            logging.info('Login Successful')
            self.token = response.SessionID
            self.populate_details(response)            
            return self.SUCCESS
        else:
            raise AuthenticationError('Unable to authenticate with Total Connect')

    def get_session_details(self):
        """Gets Details for the given session"""

        logging.info('Getting session details')

        response = self.soapClient.service.GetSessionDetails(self.token, self.applicationId, self.applicationVersion)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.GetSessionDetails(self.token, self.applicationId, self.applicationVersion)

        if response.ResultCode != self.SUCCESS:
            Exception('Unable to retrieve session details')

        return response

    def populate_details(self, response):
        """Populates system details."""

        logging.info('Populating locations')

        self.locations = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']        

    def keep_alive(self):
        """Keeps the token alive to avoid server timeouts"""

        logging.info('Initiating Keep Alive')

        response = self.soapClient.service.KeepAlive(self.token)

        if response.ResultCode != self.SUCCESS:
            self.authenticate()

        return response.ResultCode

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

        response = self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type, '-1')

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type, '-1')

        logging.info("Arm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.ARM_SUCCESS) or (response.ResultCode == self.SUCCESS):
            logging.info('System Armed')
        else:
            raise Exception('Could not disarm system')

        return self.SUCCESS

    def get_security_panel_device_id(self, location):
        """Find the device id of the security panel."""
        deviceId = False
        for device in location['DeviceList']['DeviceInfoBasic']:
            if device['DeviceName'] == 'Security Panel' or device['DeviceName'] == 'Security System' or device['DeviceName'] == 'L5100-WiFi' or device['DeviceName'] == 'Lynx Touch-WiFi':
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

    def get_panel_meta_data(self, location_name=False):
        location = self.get_location_by_location_name(location_name)
        
        response = self.soapClient.service.GetPanelMetaDataAndFullStatus(self.token, location['LocationID'], 0, 0, 1)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.GetPanelMetaDataAndFullStatus(self.token, location['LocationID'], 0, 0, 1)

        if response.ResultCode != self.SUCCESS:
            raise Exception('Could not retrieve panel meta data')

        return response


    def get_zone_status(self, location_name=False):
        """Get the status of all zones in a given location"""

        response = self.get_panel_meta_data(location_name)

        panel_meta_data = zeep.helpers.serialize_object(response)
        
        zones = panel_meta_data['PanelMetadataAndStatus']['Zones']

        return zones

    def get_armed_status(self, location_name=False):
        """Get the status of the panel."""

        response = self.get_panel_meta_data(location_name)

        panel_meta_data = zeep.helpers.serialize_object(response)

        alarm_code = panel_meta_data['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

        return alarm_code

    def is_armed(self, location_name=False):
        """Return True or False if the system is armed in any way"""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == self.ARMED_AWAY:
            return True
        elif alarm_code == self.ARMED_AWAY_BYPASS:
            return True
        elif alarm_code == self.ARMED_AWAY_INSTANT:
            return True
        elif alarm_code == self.ARMED_AWAY_INSTANT_BYPASS:
            return True
        elif alarm_code == self.ARMED_STAY:
            return True
        elif alarm_code == self.ARMED_STAY_BYPASS:
            return True
        elif alarm_code == self.ARMED_STAY_INSTANT:
            return True
        elif alarm_code == self.ARMED_STAY_INSTANT_BYPASS:
            return True
        elif alarm_code == self.ARMED_STAY_NIGHT:
            return True
        elif alarm_code == self.ARMED_CUSTOM_BYPASS:
            return True
        else:
            return False

    def is_arming(self, location_name=False):
        """Return true or false is the system is in the process of arming."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == self.ARMING:
            return True
        else:
            return False

    def is_disarming(self, location_name=False):
        """Return true or false is the system is in the process of disarming."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == self.DISARMING:
            return True
        else:
            return False

    def is_pending(self, location_name=False):
        """Return true or false is the system is pending an action."""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == self.ARMING or alarm_code == self.DISARMING:
            return True
        else:
            return False

    def disarm(self, location_name=False):
        """Disarm the system."""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        response = self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')

        logging.info("Disarm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.DISARM_SUCCESS) or (response.ResultCode == self.SUCCESS):
            logging.info('System Disarmed')
        else:
            raise Exception('Could not disarm system')

        return self.SUCCESS

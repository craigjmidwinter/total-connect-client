import zeep
import logging
import time

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4
VALID_DEVICES = ['Security Panel',
                 'Security System',
                 'L5100-WiFi',
                 'Lynx Touch-WiFi',
                 'ILP5',
                 'LTE-XV',
                 'GSMX4G',
                 'GSMVLP5-4G',
                 '7874i',
                 'GSMV4G',
                 'VISTA-21IP4G'
                 ]

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
    ALARMING = 10207
    ALARMING_FIRE_SMOKE = 10212 
    ALARMING_CARBON_MONOXIDE = 10213

    INVALID_SESSION = -102
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    CONNECTION_ERROR = 4101

    def __init__(self, username, password, usercode='-1'):
        self.soapClient = zeep.Client('https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL')

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.usercode = usercode
        self.token = False
        self._panel_meta_data = []
        self._ac_loss = False
        self._low_battery = False

        self.locations = []

        self.authenticate()
        self.get_panel_meta_data()

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

        response = self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type, self.usercode)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type, self.usercode)

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
            if device['DeviceName'] in VALID_DEVICES:
                deviceId = device['DeviceID']
            else:
                # can't raise exception because some devices should be silently ignored, like the "Wifi Doorbell" a.k.a. Skybell
                logging.info('Device name "' + device['DeviceName'] + '" not in VALID_DEVICES list.')

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

        self._panel_meta_data = zeep.helpers.serialize_object(response)
        self.ac_loss = self._panel_meta_data['PanelMetadataAndStatus'].get('IsInACLoss')
        self.low_battery = self._panel_meta_data['PanelMetadataAndStatus'].get('IsInLowBattery')

        zones = self._panel_meta_data['PanelMetadataAndStatus'].get('Zones')
        if zones != None:
            self.zones = zones.get('ZoneInfo')

        return response

    @property
    def ac_loss(self):
        """Get status of AC Loss."""
        return self._ac_loss

    @ac_loss.setter
    def ac_loss(self, new_state):
        """Set state of AC Loss flag"""
        if new_state == 'False' or new_state == False:
            self._ac_loss = False
        else:
            self._ac_loss = True

    @property
    def low_battery(self):
        """Get status of low battery"""
        return self._low_battery

    @low_battery.setter
    def low_battery(self, new_state):
        """Set state of Low Battery flag"""
        if new_state == 'False' or new_state == False:
            self._low_battery = False
        else:
            self._low_battery = True

    def connect_to_panel(self, location_name=False, attempts=3):
        """Connect to the panel"""
        location = False
        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)
        attempt =  0
        while ( attempt < attempts ):
            response = self.soapClient.service.ConnectToPanel(self.token, location['LocationID'], deviceId )
            if response.ResultCode != self.SUCCESS:
                attempt += 1
                logging.error('Could not connect to panel, retrying ' + str(attempt) + '/' + str(attempts) + '.')
                time.sleep(3)
            else:
                break
        return response

    def get_zone_state(self, location_name=False):
        """Get the states of all zones in a given location"""
        self.connect_to_panel()
        location = self.get_location_by_location_name(location_name)
        response = self.soapClient.service.GetZonesListInState(self.token, location['LocationID'], 0, 0)
        zone_list_in_state = zeep.helpers.serialize_object(response['ZoneStatus']['Zones']['ZoneStatusInfo'])

        zone_list=[]
        for item in zone_list_in_state:
            for zone in self.zones:
                if item['ZoneID']==zone['ZoneID']:
                    d = {"ZoneID":zone['ZoneID'],"ZoneDescription":zone['ZoneDescription'],"ZoneStatus":item['ZoneStatus']}
            zone_list.append(d)
        return zone_list

    def get_armed_status(self, location_name=False):
        """Get the status of the panel."""

        self.get_panel_meta_data(location_name)

        alarm_code = self._panel_meta_data['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

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

        response = self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, self.usercode)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, self.usercode)

        logging.info("Disarm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.DISARM_SUCCESS) or (response.ResultCode == self.SUCCESS):
            logging.info('System Disarmed')
        else:
            raise Exception('Could not disarm system')

        return self.SUCCESS

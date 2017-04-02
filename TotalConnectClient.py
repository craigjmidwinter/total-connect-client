import zeep
import logging

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1


class TotalConnectClient():
    DISARMED = 10200
    ARMED_STAY = 10203
    ARMED_AWAY = 10201

    def __init__(self, username, password, panel_code):
        self.soapClient = zeep.Client('https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL')

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.panel_code = panel_code
        self.token = False

        self.locations = []

        self.authenticate()

    def authenticate(self):
        """login to the system"""

        response = self.soapClient.service.AuthenticateUserLogin(self.username, self.password, self.applicationId,
                                                                 self.applicationVersion)
        if response.ResultData == 'Success':
            self.token = response.SessionID
            self.populate_details()
        else:
            Exception('Authentication Error')

    def populate_details(self):
        """populates system details"""

        response = self.soapClient.service.GetSessionDetails(self.token, self.applicationId, self.applicationVersion)

        logging.info('Getting session details')

        self.locations = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']

        logging.info('Populated locations')

    def arm_stay(self, location_name=False):
        """arm - stay"""

        self.arm(ARM_TYPE_STAY, location_name)

    def arm_away(self, location_name=False):
        """arm - away"""

        self.arm(ARM_TYPE_AWAY, location_name)

    def arm(self, arm_type, location_name=False):
        """arm system"""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.ArmSecuritySystem(self.token, location['LocationID'], deviceId, arm_type,
                                                  '-1')  # Quickarm

        logging.info('armed')

    def get_security_panel_device_id(self, location):
        """find the device id of the security panel"""
        deviceId = False
        for device in location['DeviceList']['DeviceInfoBasic']:
            if device['DeviceName'] == 'Security Panel':
                deviceId = device['DeviceID']

        if deviceId is False:
            raise Exception('No security panel found')

        return deviceId

    def get_location_by_location_name(self, location_name=False):
        """get the location object for a given name (or the default location if none is provided"""

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
        """Get the status of the panel"""
        location = self.get_location_by_location_name(location_name)

        response = self.soapClient.service.GetPanelMetaDataAndFullStatus(self.token, location['LocationID'], 0, 0, 1)

        status = zeep.helpers.serialize_object(response)

        alarm_code = status['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

        return alarm_code

    def is_armed(self, location_name=False):
        """return True or False if the system is alarmed in any way"""
        alarm_code = self.get_armed_status(location_name)

        if alarm_code == 10201 or alarm_code == 10203:
            return True
        else:
            return False


    def disarm(self, location_name=False):
        """disarm the system"""

        location = self.get_location_by_location_name(location_name)
        deviceId = self.get_security_panel_device_id(location)

        self.soapClient.service.DisarmSecuritySystem(self.token, location['LocationID'], deviceId, '-1')


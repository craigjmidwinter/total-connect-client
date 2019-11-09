"""Total Connect Client."""

import logging
import time
import zeep

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

ZONE_STATUS_NORMAL = 0
ZONE_STATUS_BYPASSED = 1
ZONE_STATUS_FAULT = 2
ZONE_STATUS_TAMPER = 8
ZONE_STATUS_TROUBLE_LOW_BATTERY = 72
ZONE_STATUS_TRIGGERED = 256

ZONE_TYPE_SECURITY = 0
ZONE_TYPE_FIRE_SMOKE = 9
ZONE_TYPE_CARBON_MONOXIDE = 14

ZONE_BYPASS_SUCCESS = 0
GET_ALL_SENSORS_MASK_STATUS_SUCCESS = 0


class AuthenticationError(Exception):
    """Authentication Error class."""
    
    def __init__(self, *args, **kwargs):
        """Initialize."""
        Exception.__init__(self, *args, **kwargs)


class TotalConnectClient:
    """Client for Total Connect."""

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
    BAD_USER_OR_PASSWORD = -50004

    MAX_REQUEST_ATTEMPTS = 10

    def __init__(self, username, password, usercode='-1'):
        """Initialize."""
        self.soapClient = zeep.Client('https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL')

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.usercode = usercode
        self.token = False
        self.locations = {}

        self.authenticate()

    def request(self, request, attempts=0):
        """Send a SOAP request."""
        base = 'self.soapClient.service.'
        response = eval(base + request)
        attempts += 1

        if attempts < self.MAX_REQUEST_ATTEMPTS:
            if response.ResultCode == self.INVALID_SESSION:
                logging.info('Invalid session (attempt number {}).'.format(attempts))
                self.authenticate()
                return self.request(request, attempts)
            elif response.ResultCode == self.CONNECTION_ERROR:
                logging.info('Connection error (attempt number {}).'.format(attempts))
                time.sleep(3)
                return self.request(request, attempts)
            return zeep.helpers.serialize_object(response)
        raise Exception('Could not execute request.  Maximum attempts tried.')

    def authenticate(self):
        """Login to the system."""
        response = self.soapClient.service.LoginAndGetSessionDetails(self.username, self.password, self.applicationId, self.applicationVersion)
        if response.ResultCode == self.SUCCESS:
            logging.info('Login Successful')
            self.token = response.SessionID
            self.populate_details(response)
            return self.SUCCESS
        elif response.ResultCode == self.BAD_USER_OR_PASSWORD:
            raise AuthenticationError('Unable to authenticate with Total Connect. Bad username or password.')
        else:
            raise AuthenticationError('Unable to authenticate with Total Connect. ResultCode: ' +
                                      str(response.ResultCode) + '. ResultData: ' + str(response.ResultData))

    def populate_details(self, response):
        """Populate system details."""
        logging.info('Populating locations')

        location_data = zeep.helpers.serialize_object(response.Locations)['LocationInfoBasic']

        for location in location_data:
            self.locations[location['LocationID']] = TotalConnectLocation(location)
            self.get_zone_details(location['LocationID'])
            self.get_panel_meta_data(location['LocationID'])

        if len(self.locations) < 1:
            Exception('No locations found!')

    def keep_alive(self):
        """Keep the token alive to avoid server timeouts."""
        logging.info('Initiating Keep Alive')

        response = self.soapClient.service.KeepAlive(self.token)

        if response.ResultCode != self.SUCCESS:
            self.authenticate()

        return response.ResultCode

    def arm_away(self, location_id):
        """Arm the system (Away)."""
        self.arm(ARM_TYPE_AWAY, location_id)

    def arm_stay(self, location_id):
        """Arm the system (Stay)."""
        self.arm(ARM_TYPE_STAY, location_id)

    def arm_stay_instant(self, location_id):
        """Arm the system (Stay - Instant)."""
        self.arm(ARM_TYPE_STAY_INSTANT, location_id)

    def arm_away_instant(self, location_id):
        """Arm the system (Away - Instant)."""
        self.arm(ARM_TYPE_AWAY_INSTANT, location_id)

    def arm_stay_night(self, location_id):
        """Arm the system (Stay - Night)."""
        self.arm(ARM_TYPE_STAY_NIGHT, location_id)

    def arm(self, arm_type, location_id):
        """Arm the system."""
        response = self.soapClient.service.ArmSecuritySystem(self.token, location_id, self.locations[location_id].security_device_id, arm_type, self.usercode)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.ArmSecuritySystem(self.token, location_id, self.locations[location_id].security_device_id, arm_type, self.usercode)

        logging.info("Arm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.ARM_SUCCESS) or (response.ResultCode == self.SUCCESS):
            logging.info('System Armed')
        else:
            raise Exception('Could not arm system. ResultCode: ' + str(response.ResultCode) +
                            '. ResultData: ' + str(response.ResultData))

        return self.SUCCESS

    def get_panel_meta_data(self, location_id):
        """Get all meta data about the alarm panel."""
        result = self.request('GetPanelMetaDataAndFullStatus(self.token, ' + str(location_id) + ', 0, 0, 1)')

        if result['ResultCode'] != self.SUCCESS:
            raise Exception('Could not retrieve panel meta data. ResultCode: ' + str(result['ResultCode']) +
                            '. ResultData: ' + str(result['ResultData']))

        if result is not None:
            self.locations[location_id].ac_loss = result['PanelMetadataAndStatus'].get('IsInACLoss')
            self.locations[location_id].low_battery = result['PanelMetadataAndStatus'].get('IsInLowBattery')
            self.locations[location_id].is_cover_tampered = result['PanelMetadataAndStatus'].get('IsCoverTampered')
            self.locations[location_id].last_updated_timestamp_ticks = result['PanelMetadataAndStatus'].get('LastUpdatedTimestampTicks')
            self.locations[location_id].configuration_sequence_number = result['PanelMetadataAndStatus'].get('ConfigurationSequenceNumber')
            self.locations[location_id].arming_state = result['PanelMetadataAndStatus']['Partitions']['PartitionInfo'][0]['ArmingState']

            zones = result['PanelMetadataAndStatus'].get('Zones')
            if zones is not None:
                zone_info = zones.get('ZoneInfo')
                if zone_info is not None:
                    for zone in zone_info:
                        if zone is not None:
                            zone_id = zone.get('ZoneID')
                            if zone_id is not None:
                                self.locations[location_id].zones[zone_id].update(zone)
        else:
            raise Exception('Panel_meta_data is empty.')

        return result

    def zone_status(self, location_id, zone_id):
        """Get status of a zone."""
        z = self.locations[location_id].zones.get(zone_id)
        if z is None:
            logging.error('Zone {} does not exist.'.format(zone_id))
            return None

        return z.status

    def get_armed_status(self, location_id):
        """Get the status of the panel."""
        self.get_panel_meta_data(location_id)
        return self.locations[location_id].arming_state

    def is_armed(self, location_id):
        """Return True or False if the system is armed in any way."""
        alarm_code = self.get_armed_status(location_id)

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
        return False

    def is_arming(self, location_id):
        """Return true or false is the system is in the process of arming."""
        return self.get_armed_status(location_id) == self.ARMING

    def is_disarming(self, location_id):
        """Return true or false is the system is in the process of disarming."""
        return self.get_armed_status(location_id) == self.DISARMING

    def is_pending(self, location_id):
        """Return true or false is the system is pending an action."""
        alarm_code = self.get_armed_status(location_id)

        if alarm_code == self.ARMING or alarm_code == self.DISARMING:
            return True
        else:
            return False

    def disarm(self, location_id):
        """Disarm the system."""
        response = self.soapClient.service.DisarmSecuritySystem(self.token, location_id, self.locations[location_id].security_device_id, self.usercode)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.DisarmSecuritySystem(self.token, location_id, self.locations[location_id].security_device_id, self.usercode)

        logging.info("Disarm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.DISARM_SUCCESS) or (response.ResultCode == self.SUCCESS):
            logging.info('System Disarmed')
        else:
            raise Exception('Could not disarm system. ResultCode: ' + str(response.ResultCode) +
                            '. ResultData: ' + str(response.ResultData))

        return self.SUCCESS

    def zone_bypass(self, zone_id, location_id):
        """Bypass a zone."""
        response = self.soapClient.service.Bypass(self.token,
                                                  location_id,
                                                  self.locations[location_id].security_device_id,
                                                  zone_id, self.usercode)

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.Bypass(self.token,
                                                      location_id,
                                                      self.locations[location_id].security_device_id,
                                                      zone_id, self.usercode)

        logging.info('Bypass Result Code: {}'.format(response.ResultCode))

        if response.ResultCode == ZONE_BYPASS_SUCCESS:
            logging.info('Zone ' + str(zone_id) + ' bypassed.')
        else:
            raise Exception('Could not bypass zone. ResultCode: ' + str(response.ResultCode) +
                            '. ResultData: ' + str(response.ResultData))

        return self.SUCCESS

    def get_zone_details(self, location_id):
        """Get Zone details."""
        result = self.request('GetZonesListInStateEx_V1(self.token, ' +
                              str(location_id) +
                              ', {"int": ["1"]}, 0)')

        if result['ResultCode'] != self.SUCCESS:
            raise Exception('Could not retrieve zone detail data. ResultCode: ' +
                            str(result['ResultCode']) +
                            '. ResultData: ' +
                            str(result['ResultData']))

        zone_status = result.get('ZoneStatus')

        if zone_status is not None:
            zones = zone_status.get('Zones')
            if zones is not None:
                zone_info = zones.get('ZoneStatusInfoWithPartitionId')
                if zone_info is not None:
                    self.locations[location_id].zones.clear()
                    for zone in zone_info:
                        if zone is not None:
                            self.locations[location_id].zones[zone.get('ZoneID')] = TotalConnectZone(zone)
        else:
            logging.error('Could not get zone details. ResultCode: {}. ResultData: {}.'
                          .format(result['ResultCode'], result['ResultData']))

        return self.SUCCESS


class TotalConnectLocation:
    """TotalConnectLocation class."""

    def __init__(self, location):
        """Initialize."""
        self.location_id = location.get('LocationID')
        self.location_name = location.get('LocationName')
        self.security_device_id = location.get('SecurityDeviceID')
        self.ac_loss = None
        self.low_battery = None
        self.is_cover_tampered = None
        self.arming_state = None
        self.zones = {}

    def __str__(self):
        """Return a texting that is printable."""
        text = 'LocationID: {}\n'.format(self.location_id)
        text = text + 'LocationName: {}\n'.format(self.location_name)
        text = text + 'SecurityDeviceID: {}\n'.format(self.security_device_id)
        text = text + 'AcLoss: {}\n'.format(self.ac_loss)
        text = text + 'LowBattery: {}\n'.format(self.low_battery)
        text = text + 'IsCoverTampered: {}\n'.format(self.is_cover_tampered)
        text = text + 'Arming State: {}\n'.format(self.arming_state)

        return text


class TotalConnectZone:
    """TotalConnectZone class."""

    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get('ZoneID')
        self.description = zone.get('ZoneDescription')
        self.status = zone.get('ZoneStatus')
        self.partition = zone.get('PartitionID')
        self.zone_type_id = zone.get('ZoneTypeId')

    def update(self, zone):
        """Update the zone."""
        if self.id == zone.get('ZoneID'):
            self.description = zone.get('ZoneDescription')
            self.partition = zone.get('PartitionID')
            self.status = zone.get('ZoneStatus')
        else:
            raise Exception('ZoneID does not match in TotalConnectZone.')

    def __str__(self):
        """Return a string that is printable."""
        text = 'ZoneID: ' + str(self.id) + '\n'
        text = text + 'ZoneDescription: ' + str(self.description) + '\n'
        text = text + 'ZoneStatus: ' + str(self.status) + '\n'
        text = text + 'ZonePartition: ' + str(self.partition) + '\n'
        text = text + 'ZoneTypeID: ' + str(self.zone_type_id) + '\n'

        return text

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
ZONE_STATUS_LOW_BATTERY = 64
ZONE_STATUS_BYPASSED_LOW_BATTERY = 65
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

    INVALID_SESSION = -102
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    CONNECTION_ERROR = 4101
    FAILED_TO_CONNECT = -4104
    BAD_USER_OR_PASSWORD = -50004
    AUTHENTICATION_FAILED = -100

    MAX_REQUEST_ATTEMPTS = 10

    def __init__(self, username, password, usercode="-1", auto_bypass_battery=False):
        """Initialize."""
        self.soapClient = zeep.Client("https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL")
        self.soap_base = "self.soapClient.service."

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.usercode = usercode
        self.auto_bypass_low_battery = auto_bypass_battery
        self.token = False
        self.locations = {}

        self.authenticate()

    def request(self, request, attempts=0):
        """Send a SOAP request."""
        if attempts < self.MAX_REQUEST_ATTEMPTS:
            attempts += 1
            response = eval(self.soap_base + request)

            if response.ResultCode == self.SUCCESS:
                return zeep.helpers.serialize_object(response)
            if response.ResultCode == self.INVALID_SESSION:
                logging.info(
                    "total-connect-client invalid session (attempt number {}).".format(
                        attempts
                    )
                )
                self.authenticate()
                return self.request(request, attempts)
            if response.ResultCode == self.CONNECTION_ERROR:
                logging.info(
                    "total-connect-client connection error (attempt number {}).".format(
                        attempts
                    )
                )
                time.sleep(3)
                return self.request(request, attempts)
            if response.ResultCode == self.FAILED_TO_CONNECT:
                logging.info(
                    "total-connect-client failed to connect with security system (attempt number {}).".format(
                        attempts
                    )
                )
                time.sleep(3)
                return self.request(request, attempts)
            if response.ResultCode == self.AUTHENTICATION_FAILED:
                logging.info(
                    "total-connect-client authentication failed (attempt number {}).".format(
                        attempts
                    )
                )
                time.sleep(3)
                return self.request(request, attempts)
            if response.ResultCode == self.BAD_USER_OR_PASSWORD:
                raise AuthenticationError("total-connect-client bad user or password.")

        raise Exception(
            "total-connect-client could not execute request.  Maximum attempts tried."
        )

    def authenticate(self):
        """Login to the system."""
        response = self.request(
            "LoginAndGetSessionDetails(self.username, self.password, self.applicationId, self.applicationVersion)"
        )

        if response["ResultCode"] == self.SUCCESS:
            logging.info("Login Successful")
            self.token = response["SessionID"]
            self.populate_details(response)
            return self.SUCCESS
        else:
            raise AuthenticationError(
                "Unable to authenticate with Total Connect. ResultCode: "
                + str(response.ResultCode)
                + ". ResultData: "
                + str(response.ResultData)
            )

    def populate_details(self, response):
        """Populate system details."""
        logging.info("total-connect-client populating locations")

        # not currently using info: ModuleFlags, UserInfo

        location_data = response["Locations"]["LocationInfoBasic"]

        for location in location_data:
            location_id = location["LocationID"]
            self.locations[location_id] = TotalConnectLocation(location, self)
            self.get_zone_details(location_id)
            self.get_panel_meta_data(location_id)

        if len(self.locations) < 1:
            Exception("No locations found!")

    def keep_alive(self):
        """Keep the token alive to avoid server timeouts."""
        logging.info("total-connect-client initiating Keep Alive")

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
        response = self.soapClient.service.ArmSecuritySystem(
            self.token,
            location_id,
            self.locations[location_id].security_device_id,
            arm_type,
            self.usercode,
        )

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.ArmSecuritySystem(
                self.token,
                location_id,
                self.locations[location_id].security_device_id,
                arm_type,
                self.usercode,
            )

        logging.info("Arm Result Code:" + str(response.ResultCode))

        if response.ResultCode in (self.ARM_SUCCESS, self.SUCCESS):
            logging.info("System Armed")
        else:
            raise Exception(
                "Could not arm system. ResultCode: "
                + str(response.ResultCode)
                + ". ResultData: "
                + str(response.ResultData)
            )

        return self.SUCCESS

    def get_panel_meta_data(self, location_id):
        """Get all meta data about the alarm panel."""
        result = self.request(
            "GetPanelMetaDataAndFullStatus(self.token, "
            + str(location_id)
            + ", 0, 0, 1)"
        )

        if result["ResultCode"] != self.SUCCESS:
            raise Exception(
                "Could not retrieve panel meta data. ResultCode: "
                + str(result["ResultCode"])
                + ". ResultData: "
                + str(result["ResultData"])
            )

        if result is not None:

            self.locations[location_id].set_status(result["PanelMetadataAndStatus"])

        else:
            raise Exception("Panel_meta_data is empty.")

        return result

    def zone_status(self, location_id, zone_id):
        """Get status of a zone."""
        z = self.locations[location_id].zones.get(zone_id)
        if z is None:
            logging.error("Zone {} does not exist.".format(zone_id))
            return None

        return z.status

    def get_armed_status(self, location_id):
        """Get the status of the panel."""
        self.get_panel_meta_data(location_id)
        return self.locations[location_id].arming_state

    def disarm(self, location_id):
        """Disarm the system."""
        response = self.soapClient.service.DisarmSecuritySystem(
            self.token,
            location_id,
            self.locations[location_id].security_device_id,
            self.usercode,
        )

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.DisarmSecuritySystem(
                self.token,
                location_id,
                self.locations[location_id].security_device_id,
                self.usercode,
            )

        logging.info("Disarm Result Code:" + str(response.ResultCode))

        if (response.ResultCode == self.DISARM_SUCCESS) or (
            response.ResultCode == self.SUCCESS
        ):
            logging.info("System Disarmed")
        else:
            raise Exception(
                "Could not disarm system. ResultCode: "
                + str(response.ResultCode)
                + ". ResultData: "
                + str(response.ResultData)
            )

        return self.SUCCESS

    def zone_bypass(self, zone_id, location_id):
        """Bypass a zone."""
        response = self.soapClient.service.Bypass(
            self.token,
            location_id,
            self.locations[location_id].security_device_id,
            zone_id,
            self.usercode,
        )

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.Bypass(
                self.token,
                location_id,
                self.locations[location_id].security_device_id,
                zone_id,
                self.usercode,
            )

        logging.info("Bypass Result Code: {}".format(response.ResultCode))

        if response.ResultCode == ZONE_BYPASS_SUCCESS:
            self.locations[location_id].zones[zone_id].bypass()
        else:
            raise Exception(
                "Could not bypass zone. ResultCode: "
                + str(response.ResultCode)
                + ". ResultData: "
                + str(response.ResultData)
            )

        return self.SUCCESS

    def get_zone_details(self, location_id):
        """Get Zone details."""
        result = self.request(
            "GetZonesListInStateEx_V1(self.token, "
            + str(location_id)
            + ', {"int": ["1"]}, 0)'
        )

        if result["ResultCode"] != self.SUCCESS:
            raise Exception(
                "Could not retrieve zone detail data. ResultCode: "
                + str(result["ResultCode"])
                + ". ResultData: "
                + str(result["ResultData"])
            )

        zone_status = result.get("ZoneStatus")

        if zone_status is not None:
            zones = zone_status.get("Zones")
            if zones is not None:
                zone_info = zones.get("ZoneStatusInfoWithPartitionId")
                if zone_info is not None:
                    self.locations[location_id].zones.clear()
                    for zone in zone_info:
                        if zone is not None:
                            self.locations[location_id].zones[
                                zone.get("ZoneID")
                            ] = TotalConnectZone(zone)
        else:
            logging.error(
                "Could not get zone details. ResultCode: {}. ResultData: {}.".format(
                    result["ResultCode"], result["ResultData"]
                )
            )

        return self.SUCCESS


class TotalConnectLocation:
    """TotalConnectLocation class."""

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

    def __init__(self, location_info_basic, parent):
        """Initialize based on a 'LocationInfoBasic'."""
        # currently not using info from LocationModuleFlags, DeviceList
        self.location_id = location_info_basic.get("LocationID")
        self.location_name = location_info_basic.get("LocationName")
        self.security_device_id = location_info_basic.get("SecurityDeviceID")
        self.parent = parent
        self.ac_loss = None
        self.low_battery = None
        self.cover_tampered = None
        self.last_updated_timestamp_ticks = None
        self.configuration_sequence_number = None
        self.arming_state = None
        self.zones = {}

    def __str__(self):
        """Return a text string that is printable."""
        text = "LocationID: {}\n".format(self.location_id)
        text = text + "LocationName: {}\n".format(self.location_name)
        text = text + "SecurityDeviceID: {}\n".format(self.security_device_id)
        text = text + "AcLoss: {}\n".format(self.ac_loss)
        text = text + "LowBattery: {}\n".format(self.low_battery)
        text = text + "IsCoverTampered: {}\n".format(self.cover_tampered)
        text = text + "Arming State: {}\n".format(self.arming_state)

        return text

    def set_status(self, data):
        """Update status based on a 'PanelMetadataAndStatus'."""
        self.ac_loss = data.get("IsInACLoss")
        self.low_battery = data.get("IsInLowBattery")
        self.is_cover_tampered = data.get("IsCoverTampered")
        self.last_updated_timestamp_ticks = data.get("LastUpdatedTimestampTicks")
        self.configuration_sequence_number = data.get("ConfigurationSequenceNumber")
        self.arming_state = data["Partitions"]["PartitionInfo"][0]["ArmingState"]

        zones = data.get("Zones")
        if zones is not None:
            zone_info = zones.get("ZoneInfo")
            if zone_info is not None:
                for zone in zone_info:
                    if zone is not None:
                        zone_id = zone.get("ZoneID")
                        if zone_id is not None:
                            self.zones[zone_id].update(zone)
                            if (
                                self.zones[zone_id].is_low_battery()
                                and self.parent.auto_bypass_low_battery
                            ):
                                self.parent.zone_bypass(zone_id, self.location_id)

    def is_low_battery(self):
        """Return true if low battery."""
        return self.low_battery is True

    def is_ac_loss(self):
        """Return true if AC loss."""
        return self.ac_loss is True

    def is_cover_tampered(self):
        """Return true if cover is tampered."""
        return self.cover_tampered is True

    def is_arming(self):
        """Return true if the system is in the process of arming."""
        return self.arming_state == self.ARMING

    def is_disarming(self):
        """Return true if the system is in the process of disarming."""
        return self.arming_state == self.DISARMING

    def is_pending(self, location_id):
        """Return true if the system is pending an action."""
        return self.is_disarming() or self.is_arming()

    def is_disarmed(self):
        """Return True if the system is disarmed."""
        return self.arming_state in (self.DISARMED, self.DISARMED_BYPASS)

    def is_armed_away(self):
        """Return True if the system is armed away in any way."""
        return self.arming_state in (
            self.ARMED_AWAY,
            self.ARMED_AWAY_BYPASS,
            self.ARMED_AWAY_INSTANT,
            self.ARMED_AWAY_INSTANT_BYPASS,
        )

    def is_armed_custom_bypass(self):
        """Return True if the system is armed custom bypass in any way."""
        return self.arming_state == self.ARMED_CUSTOM_BYPASS

    def is_armed_home(self):
        """Return True if the system is armed home/stay in any way."""
        return self.arming_state in (
            self.ARMED_STAY,
            self.ARMED_STAY_BYPASS,
            self.ARMED_STAY_INSTANT,
            self.ARMED_STAY_INSTANT_BYPASS,
            self.ARMED_STAY_NIGHT,
        )

    def is_armed_night(self):
        """Return True if the system is armed night in any way."""
        return self.arming_state == self.ARMED_STAY_NIGHT

    def is_armed(self):
        """Return True if the system is armed in any way."""
        return (
            self.is_armed_away()
            or self.is_armed_custom_bypass()
            or self.is_armed_home()
            or self.is_armed_night()
        )

    def is_triggered_police(self):
        """Return True if the system is triggered for police or medical."""
        return self.arming_state == self.ALARMING

    def is_triggered_fire(self):
        """Return True if the system is triggered for fire or smoke."""
        return self.arming_state == self.ALARMING_FIRE_SMOKE

    def is_triggered_gas(self):
        """Return True if the system is triggered for carbon monoxide."""
        return self.arming_state == self.ALARMING_CARBON_MONOXIDE

    def is_triggered(self):
        """Return True if the system is triggered in any way."""
        return (
            self.is_triggered_fire()
            or self.is_triggered_gas()
            or self.is_triggered_police()
        )


class TotalConnectZone:
    """TotalConnectZone class."""

    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get("ZoneID")
        self.description = zone.get("ZoneDescription")
        self.status = zone.get("ZoneStatus")
        self.partition = zone.get("PartitionID")
        self.zone_type_id = zone.get("ZoneTypeId")
        self.can_be_bypassed = zone.get("CanBeBypassed")

    def update(self, zone):
        """Update the zone."""
        if self.id == zone.get("ZoneID"):
            self.description = zone.get("ZoneDescription")
            self.partition = zone.get("PartitionID")
            self.status = zone.get("ZoneStatus")
        else:
            raise Exception("ZoneID does not match in TotalConnectZone.")

    def __str__(self):
        """Return a string that is printable."""
        text = "ZoneID: " + str(self.id) + "\n"
        text = text + "ZoneDescription: " + str(self.description) + "\n"
        text = text + "ZoneStatus: " + str(self.status) + "\n"
        text = text + "ZonePartition: " + str(self.partition) + "\n"
        text = text + "ZoneTypeID: " + str(self.zone_type_id) + "\n"

        return text

    def is_bypassed(self):
        """Return true if the zone is bypassed."""
        return self.status in (ZONE_STATUS_BYPASSED, ZONE_STATUS_BYPASSED_LOW_BATTERY)

    def bypass(self):
        """Set is_bypassed status."""
        self.status = ZONE_STATUS_BYPASSED

    def is_faulted(self):
        """Return true if the zone is faulted."""
        return self.status == ZONE_STATUS_FAULT

    def is_tampered(self):
        """Return true if zone is tampered."""
        return self.status == ZONE_STATUS_TAMPER

    def is_low_battery(self):
        """Return true if low battery."""
        return self.status in (
            ZONE_STATUS_LOW_BATTERY,
            ZONE_STATUS_BYPASSED_LOW_BATTERY,
            ZONE_STATUS_TROUBLE_LOW_BATTERY,
        )

    def is_troubled(self):
        """Return true if zone is troubled."""
        return self.status == ZONE_STATUS_TROUBLE_LOW_BATTERY

    def is_triggered(self):
        """Return true if zone is triggered."""
        return self.status == ZONE_STATUS_TRIGGERED

    def is_type_button(self):
        """Return true if zone is a button."""
        return self.zone_type_id == ZONE_TYPE_SECURITY and self.can_be_bypassed == 0

    def is_type_security(self):
        """Return true if zone type is security."""
        return self.zone_type_id == ZONE_TYPE_SECURITY

    def is_type_fire(self):
        """Return true if zone type is fire or smoke."""
        return self.zone_type_id == ZONE_TYPE_FIRE_SMOKE

    def is_type_carbon_monoxide(self):
        """Return true if zone type is carbon monoxide."""
        return self.zone_type_id == ZONE_TYPE_CARBON_MONOXIDE

"""Testing constants."""
import TotalConnectClient

PASSWORD_BAD = "none"
USERNAME_BAD = "none"

LOCATION_INFO_BASIC_NORMAL = {
    "LocationID": "123456",
    "LocationName": "Home",
    "SecurityDeviceID": "987654",
    "PhotoURL": "http://www.example.com/some/path/to/file.jpg",
    "LocationModuleFlags": "Security=1,Video=0,Automation=0,GPS=0,VideoPIR=0",
    "DeviceList": None,
}

LOCATIONS = {"LocationInfoBasic": [LOCATION_INFO_BASIC_NORMAL]}

MODULE_FLAGS = "Some=0,Fake=1,Flags=2"

USER = {
    "UserID": "1234567",
    "Username": "username",
    "UserFeatureList": "Master=0,User Administration=0,Configuration Administration=0",
}


ZONE_NORMAL = {
    "ZoneID": "1",
    "ZoneDescription": "Normal",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_NORMAL,
    "PartitionId": "1",
}

ZONE_INFO = []
ZONE_INFO.append(ZONE_NORMAL)
ZONES = {"ZoneInfo": ZONE_INFO}

ZONE_STATUS_NORMAL = {
    "PartitionId": "1",
    "Batterylevel": "-1",
    "Signalstrength": "-1",
    "zoneAdditionalInfo": None,
    "ZoneID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_NORMAL,
    "ZoneTypeId": TotalConnectClient.ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneFlags": None,
}

ZONE_STATUS_INFO = []
ZONE_STATUS_INFO.append(ZONE_STATUS_NORMAL)

ZONES = {"ZoneStatusInfoWithPartitionId": ZONE_STATUS_INFO}

ZONE_STATUS = {"Zones": ZONES}

RESPONSE_GET_ZONE_DETAILS_SUCCESS = {
    "ResultCode": 0,
    "ResultData": "Success",
    "ZoneStatus": ZONE_STATUS,
}

PARTITION_DISARMED = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.DISARMED,
}

PARTITION_ARMED_STAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.ARMED_STAY,
}

PARTITION_ARMED_AWAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.ARMED_AWAY,
}

PARTITION_INFO_DISARMED = {}
PARTITION_INFO_DISARMED[0] = PARTITION_DISARMED

PARTITION_INFO_ARMED_STAY = {}
PARTITION_INFO_ARMED_STAY[0] = PARTITION_ARMED_STAY

PARTITION_INFO_ARMED_AWAY = {}
PARTITION_INFO_ARMED_AWAY[0] = PARTITION_ARMED_AWAY

PARTITIONS_DISARMED = {"PartitionInfo": PARTITION_INFO_DISARMED}
PARTITIONS_ARMED_STAY = {"PartitionInfo": PARTITION_INFO_ARMED_STAY}
PARTITIONS_ARMED_AWAY = {"PartitionInfo": PARTITION_INFO_ARMED_AWAY}

METADATA_DISARMED = {
    "Partitions": PARTITIONS_DISARMED,
    "Zones": ZONES,
    "PromptForImportSecuritySettings": False,
    "IsInACLoss": False,
    "IsCoverTampered": False,
    "Bell1SupervisionFailure": False,
    "Bell2SupervisionFailure": False,
    "IsInLowBattery": False,
}

METADATA_ARMED_STAY = METADATA_DISARMED.copy()
METADATA_ARMED_STAY["Partitions"] = PARTITIONS_ARMED_STAY

METADATA_ARMED_AWAY = METADATA_DISARMED.copy()
METADATA_ARMED_AWAY["Partitions"] = PARTITIONS_ARMED_AWAY

RESPONSE_DISARMED = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_DISARMED}
RESPONSE_ARMED_STAY = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_ARMED_STAY}
RESPONSE_ARMED_AWAY = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_ARMED_AWAY}

RESPONSE_AUTHENTICATE = {
    "ResultCode": 0,
    "SessionID": 1,
    "Locations": LOCATIONS,
    "ModuleFlags": MODULE_FLAGS,
    "UserInfo": USER,
}

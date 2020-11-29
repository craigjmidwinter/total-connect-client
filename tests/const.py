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

ZONE_STATUS_LYRIC_CONTACT = ZONE_STATUS_NORMAL.copy()
ZONE_STATUS_LYRIC_CONTACT["ZoneTypeId"] = TotalConnectClient.ZONE_TYPE_LYRIC_CONTACT

ZONE_STATUS_LYRIC_MOTION = ZONE_STATUS_NORMAL.copy()
ZONE_STATUS_LYRIC_MOTION["ZoneTypeId"] = TotalConnectClient.ZONE_TYPE_LYRIC_MOTION

ZONE_STATUS_LYRIC_POLICE = ZONE_STATUS_NORMAL.copy()
ZONE_STATUS_LYRIC_POLICE["ZoneTypeId"] = TotalConnectClient.ZONE_TYPE_LYRIC_POLICE

ZONE_STATUS_LYRIC_TEMP = ZONE_STATUS_NORMAL.copy()
ZONE_STATUS_LYRIC_TEMP["ZoneTypeId"] = TotalConnectClient.ZONE_TYPE_LYRIC_TEMP

ZONE_STATUS_LYRIC_LOCAL_ALARM = ZONE_STATUS_NORMAL.copy()
ZONE_STATUS_LYRIC_LOCAL_ALARM[
    "ZoneTypeId"
] = TotalConnectClient.ZONE_TYPE_LYRIC_LOCAL_ALARM


ZONE_STATUS_INFO = []
ZONE_STATUS_INFO.append(ZONE_STATUS_NORMAL)

ZONES = {"ZoneStatusInfoWithPartitionId": ZONE_STATUS_INFO}

ZONE_STATUS = {"Zones": ZONES}

RESPONSE_GET_ZONE_DETAILS_SUCCESS = {
    "ResultCode": 0,
    "ResultData": "Success",
    "ZoneStatus": ZONE_STATUS,
}

RESPONSE_GET_ZONE_DETAILS_NONE = RESPONSE_GET_ZONE_DETAILS_SUCCESS.copy()
RESPONSE_GET_ZONE_DETAILS_NONE["ZoneStatus"] = None

PARTITION_DISARMED = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.DISARMED,
}

PARTITION_ARMED_STAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.ARMED_STAY,
}

PARTITION_ARMED_STAY_NIGHT = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.ARMED_STAY_NIGHT,
}

PARTITION_ARMED_AWAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectClient.TotalConnectLocation.ARMED_AWAY,
}

PARTITION_INFO_DISARMED = {}
PARTITION_INFO_DISARMED[0] = PARTITION_DISARMED

PARTITION_INFO_ARMED_STAY = {}
PARTITION_INFO_ARMED_STAY[0] = PARTITION_ARMED_STAY

PARTITION_INFO_ARMED_STAY_NIGHT = {}
PARTITION_INFO_ARMED_STAY_NIGHT[0] = PARTITION_ARMED_STAY_NIGHT

PARTITION_INFO_ARMED_AWAY = {}
PARTITION_INFO_ARMED_AWAY[0] = PARTITION_ARMED_AWAY

PARTITIONS_DISARMED = {"PartitionInfo": PARTITION_INFO_DISARMED}
PARTITIONS_ARMED_STAY = {"PartitionInfo": PARTITION_INFO_ARMED_STAY}
PARTITIONS_ARMED_STAY_NIGHT = {"PartitionInfo": PARTITION_INFO_ARMED_STAY_NIGHT}
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

METADATA_ARMED_STAY_NIGHT = METADATA_DISARMED.copy()
METADATA_ARMED_STAY_NIGHT["Partitions"] = PARTITIONS_ARMED_STAY_NIGHT

METADATA_ARMED_AWAY = METADATA_DISARMED.copy()
METADATA_ARMED_AWAY["Partitions"] = PARTITIONS_ARMED_AWAY

RESPONSE_DISARMED = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_DISARMED}
RESPONSE_ARMED_STAY = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_ARMED_STAY}
RESPONSE_ARMED_STAY_NIGHT = {
    "ResultCode": 0,
    "PanelMetadataAndStatus": METADATA_ARMED_STAY_NIGHT,
}
RESPONSE_ARMED_AWAY = {"ResultCode": 0, "PanelMetadataAndStatus": METADATA_ARMED_AWAY}

RESPONSE_AUTHENTICATE = {
    "ResultCode": 0,
    "SessionID": 1,
    "Locations": LOCATIONS,
    "ModuleFlags": MODULE_FLAGS,
    "UserInfo": USER,
}

RESPONSE_BAD_USER_OR_PASSWORD = {
    "ResultCode": TotalConnectClient.TotalConnectClient.BAD_USER_OR_PASSWORD,
    "ResultData": "testing bad user or password",
}

RESPONSE_INVALID_SESSION = {
    "ResultCode": TotalConnectClient.TotalConnectClient.INVALID_SESSION,
    "ResultData": "testing invalid session",
}

RESPONSE_FAILED_TO_CONNECT = {
    "ResultCode": TotalConnectClient.TotalConnectClient.FAILED_TO_CONNECT,
    "ResultData": "testing failed to connect",
}

RESPONSE_CONNECTION_ERROR = {
    "ResultCode": TotalConnectClient.TotalConnectClient.CONNECTION_ERROR,
    "ResultData": "testing connection error",
}


RESPONSE_SESSION_INITIATED = {
    "ResultCode": TotalConnectClient.TotalConnectClient.SESSION_INITIATED,
    "ResultData": "testing session initiated",
}

RESPONSE_FEATURE_NOT_SUPPORTED = {
    "ResultCode": TotalConnectClient.TotalConnectClient.FEATURE_NOT_SUPPORTED,
    "ResultData": "testing user code feature not supported",
}

RESPONSE_UNKNOWN = {
    "ResultCode": -123456,
    "ResultData": "testing unknown result code",
}

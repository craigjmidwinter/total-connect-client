"""Testing constants."""
from total_connect_client.client import TotalConnectClient
from total_connect_client.location import TotalConnectLocation
from total_connect_client.partition import TotalConnectPartition
from total_connect_client.zone import (
    ZONE_STATUS_LOW_BATTERY,
    ZONE_STATUS_NORMAL,
    ZONE_TYPE_LYRIC_CONTACT,
    ZONE_TYPE_LYRIC_LOCAL_ALARM,
    ZONE_TYPE_LYRIC_MOTION,
    ZONE_TYPE_LYRIC_POLICE,
    ZONE_TYPE_LYRIC_TEMP,
    ZONE_TYPE_SECURITY,
)

PASSWORD_BAD = "none"
USERNAME_BAD = "none"

DEVICE_INFO_BASIC_1 = {
    "DeviceID": 1234567,
    "DeviceName": "test",
    "DeviceClassID": 1,
    "DeviceSerialNumber": "987654321ABC",
    "DeviceFlags": "PromptForUserCode=0,PromptForInstallerCode=0,PromptForImportSecuritySettings=0,AllowUserSlotEditing=0,CalCapable=1,CanBeSentToPanel=0,CanArmNightStay=0,CanSupportMultiPartition=0,PartitionCount=0,MaxPartitionCount=0,OnBoardingSupport=0,PartitionAdded=0,DuplicateUserSyncStatus=0,PanelType=8,PanelVariant=1,BLEDisarmCapable=0,ArmHomeSupported=0,DuplicateUserCodeCheck=1,CanSupportRapid=0,IsKeypadSupported=1,WifiEnrollmentSupported=0,IsConnectedPanel=0,ArmNightInSceneSupported=0,BuiltInCameraSettingsSupported=0,ZWaveThermostatScheduleDisabled=0,MultipleAuthorityLevelSupported=0,VideoOnPanelSupported=0,EnableBLEMode=0,IsPanelWiFiResetSupported=0,IsCompetitorClearBypass=0,IsNotReadyStateSupported=0,isArmStatusWithoutExitDelayNotSupported=0",
    "SecurityPanelTypeID": None,
    "DeviceSerialText": None,
}
DEVICE_LIST = []
DEVICE_LIST.append(DEVICE_INFO_BASIC_1)

LOCATION_INFO_BASIC_NORMAL = {
    "LocationID": "123456",
    "LocationName": "Home",
    "SecurityDeviceID": "987654",
    "PhotoURL": "http://www.example.com/some/path/to/file.jpg",
    "LocationModuleFlags": "Security=1,Video=0,Automation=0,GPS=0,VideoPIR=0",
    "DeviceList": { "DeviceInfoBasic": DEVICE_LIST },
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
    "ZoneStatus": ZONE_STATUS_NORMAL,
    "PartitionID": "1",
}

ZONE_LOW_BATTERY = {
    "ZoneID": "1",
    "ZoneDescription": "Low Battery",
    "PartitionID": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZONE_STATUS_LOW_BATTERY,
}

ZONE_INFO = []
ZONE_INFO.append(ZONE_NORMAL)

ZONE_INFO_LOW_BATTERY = []
ZONE_INFO_LOW_BATTERY.append(ZONE_LOW_BATTERY)

ZONES = {"ZoneInfo": ZONE_INFO}
ZONES_LOW_BATTERY = {"ZoneInfo": ZONE_INFO_LOW_BATTERY}
ZS_NORMAL = {
    "PartitionId": "1",
    "Batterylevel": "-1",
    "Signalstrength": "-1",
    "zoneAdditionalInfo": None,
    "ZoneID": "1",
    "ZoneStatus": ZONE_STATUS_NORMAL,
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneFlags": None,
}

ZONE_STATUS_LYRIC_CONTACT = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_CONTACT["ZoneTypeId"] = ZONE_TYPE_LYRIC_CONTACT

ZONE_STATUS_LYRIC_MOTION = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_MOTION["ZoneTypeId"] = ZONE_TYPE_LYRIC_MOTION

ZONE_STATUS_LYRIC_POLICE = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_POLICE["ZoneTypeId"] = ZONE_TYPE_LYRIC_POLICE

ZONE_STATUS_LYRIC_TEMP = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_TEMP["ZoneTypeId"] = ZONE_TYPE_LYRIC_TEMP

ZONE_STATUS_LYRIC_LOCAL_ALARM = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_LOCAL_ALARM["ZoneTypeId"] = ZONE_TYPE_LYRIC_LOCAL_ALARM


ZONE_STATUS_INFO = []
ZONE_STATUS_INFO.append(ZS_NORMAL)

ZONE_DETAILS = {"ZoneStatusInfoWithPartitionId": ZONE_STATUS_INFO}

ZONE_DETAIL_STATUS = {"Zones": ZONE_DETAILS}

RESPONSE_GET_ZONE_DETAILS_SUCCESS = {
    "ResultCode": 0,
    "ResultData": "Success",
    "ZoneStatus": ZONE_DETAIL_STATUS,
}

RESPONSE_GET_ZONE_DETAILS_NONE = RESPONSE_GET_ZONE_DETAILS_SUCCESS.copy()
RESPONSE_GET_ZONE_DETAILS_NONE["ZoneStatus"] = None

PARTITION_DISARMED = {
    "PartitionID": "1",
    "ArmingState": TotalConnectLocation.DISARMED,
}

PARTITION_DISARMED2 = {
    "PartitionID": "2",
    "ArmingState": TotalConnectLocation.DISARMED,
}

PARTITION_ARMED_STAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectLocation.ARMED_STAY,
}

PARTITION_ARMED_STAY_NIGHT = {
    "PartitionID": "1",
    "ArmingState": TotalConnectLocation.ARMED_STAY_NIGHT,
}

PARTITION_ARMED_AWAY = {
    "PartitionID": "1",
    "ArmingState": TotalConnectLocation.ARMED_AWAY,
}

PARTITION_INFO_DISARMED = [PARTITION_DISARMED, PARTITION_DISARMED2]

PARTITION_INFO_ARMED_STAY = [PARTITION_ARMED_STAY]

PARTITION_INFO_ARMED_STAY_NIGHT = [PARTITION_ARMED_STAY_NIGHT]

PARTITION_INFO_ARMED_AWAY = [PARTITION_ARMED_AWAY]

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

METADATA_DISARMED_LOW_BATTERY = {
    "Partitions": PARTITIONS_DISARMED,
    "Zones": ZONES_LOW_BATTERY,
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

RESPONSE_DISARMED = {
    "ResultCode": 0,
    "ResultData": "Success",
    "PanelMetadataAndStatus": METADATA_DISARMED,
    "ArmingState": TotalConnectLocation.DISARMED,
}
RESPONSE_ARMED_STAY = {
    "ResultCode": 0,
    "ResultData": "Success",
    "PanelMetadataAndStatus": METADATA_ARMED_STAY,
    "ArmingState": TotalConnectLocation.ARMED_STAY,
}
RESPONSE_ARMED_STAY_NIGHT = {
    "ResultCode": 0,
    "PanelMetadataAndStatus": METADATA_ARMED_STAY_NIGHT,
    "ArmingState": TotalConnectLocation.ARMED_STAY_NIGHT,
}
RESPONSE_ARMED_AWAY = {
    "ResultCode": 0,
    "ResultData": "Success",
    "PanelMetadataAndStatus": METADATA_ARMED_AWAY,
    "ArmingState": TotalConnectLocation.ARMED_AWAY,
}

RESPONSE_AUTHENTICATE = {
    "ResultCode": 0,
    "ResultData": "Success",
    "SessionID": 1,
    "Locations": LOCATIONS,
    "ModuleFlags": MODULE_FLAGS,
    "UserInfo": USER,
}

RESPONSE_AUTHENTICATE_EMPTY = RESPONSE_AUTHENTICATE.copy()
RESPONSE_AUTHENTICATE_EMPTY["Locations"] = None

RESPONSE_BAD_USER_OR_PASSWORD = {
    "ResultCode": TotalConnectClient.BAD_USER_OR_PASSWORD,
    "ResultData": "testing bad user or password",
}

RESPONSE_INVALID_SESSION = {
    "ResultCode": TotalConnectClient.INVALID_SESSION,
    "ResultData": "testing invalid session",
}

RESPONSE_FAILED_TO_CONNECT = {
    "ResultCode": TotalConnectClient.FAILED_TO_CONNECT,
    "ResultData": "testing failed to connect",
}

RESPONSE_CONNECTION_ERROR = {
    "ResultCode": TotalConnectClient.CONNECTION_ERROR,
    "ResultData": "testing connection error",
}


RESPONSE_SESSION_INITIATED = {
    "ResultCode": TotalConnectClient.SESSION_INITIATED,
    "ResultData": "testing session initiated",
}

RESPONSE_FEATURE_NOT_SUPPORTED = {
    "ResultCode": TotalConnectClient.FEATURE_NOT_SUPPORTED,
    "ResultData": "testing user code feature not supported",
}

RESPONSE_UNKNOWN = {
    "ResultCode": -123456,
    "ResultData": "testing unknown result code",
}

PARTITION_DETAILS_1 = {
    "PartitionID": 1,
    "ArmingState": TotalConnectPartition.DISARMED,
    "PartitionName": "Test1",
}

PARTITION_DETAILS_2 = {
    "PartitionID": 2,
    "ArmingState": TotalConnectPartition.DISARMED,
    "PartitionName": "Test2",
}

PARTITION_DETAILS = { "PartitionDetails": [PARTITION_DETAILS_1] }

RESPONSE_PARTITION_DETAILS = {
    "ResultCode": TotalConnectClient.SUCCESS,
    "ResultData": "testing partition details",
    "PartitionsInfoList": PARTITION_DETAILS,
}

PARTITION_DETAILS_TWO = { "PartitionDetails": [PARTITION_DETAILS_1, PARTITION_DETAILS_2] }
RESPONSE_PARTITION_DETAILS_TWO = {
    "ResultCode": TotalConnectClient.SUCCESS,
    "ResultData": "testing partition details",
    "PartitionsInfoList": PARTITION_DETAILS_TWO,
}

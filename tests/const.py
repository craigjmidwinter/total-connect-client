"""Testing constants."""

import copy
import jwt

from total_connect_client import ArmingState, ZoneType, ZoneStatus
from total_connect_client.const import _ResultCode

PASSWORD_BAD = "none"
USERNAME_BAD = "none"

DEVICE_INFO_BASIC_1 = {
    "DeviceID": 1234567,
    "DeviceName": "test",
    "DeviceClassID": 1,
    "DeviceSerialNumber": "987654321ABC",
    "DeviceFlags": "PromptForUserCode=0,PromptForInstallerCode=0,PromptForImportSecuritySettings=0,AllowUserSlotEditing=0,CalCapable=1,CanBeSentToPanel=0,CanArmNightStay=0,CanSupportMultiPartition=0,PartitionCount=0,MaxPartitionCount=0,OnBoardingSupport=0,PartitionAdded=0,DuplicateUserSyncStatus=0,PanelType=8,PanelVariant=1,BLEDisarmCapable=0,ArmHomeSupported=0,DuplicateUserCodeCheck=1,CanSupportRapid=0,IsKeypadSupported=1,WifiEnrollmentSupported=0,IsConnectedPanel=0,ArmNightInSceneSupported=0,BuiltInCameraSettingsSupported=0,ZWaveThermostatScheduleDisabled=0,MultipleAuthorityLevelSupported=0,VideoOnPanelSupported=0,EnableBLEMode=0,IsPanelWiFiResetSupported=0,IsCompetitorClearBypass=0,IsNotReadyStateSupported=0,isArmStatusWithoutExitDelayNotSupported=0",  # noqa: E501
    "SecurityPanelTypeID": None,
    "DeviceSerialText": None,
}
DEVICE_LIST = []
DEVICE_LIST.append(DEVICE_INFO_BASIC_1)

LOCATION_INFO_BASIC_NORMAL = {
    "LocationID": 123456,
    "LocationName": "Home",
    "SecurityDeviceID": 987654,
    "PhotoURL": "http://www.example.com/some/path/to/file.jpg",
    "LocationModuleFlags": "Security=1,Video=0,Automation=0,GPS=0,VideoPIR=0",
    "DeviceList": DEVICE_LIST,
}

LOCATIONS = [LOCATION_INFO_BASIC_NORMAL]

MODULE_FLAGS = "Some=0,Fake=1,Flags=2"

USER = {
    "UserID": "1234567",
    "Username": "username",
    "UserFeatureList": "Master=0,User Administration=0,Configuration Administration=0",
}


ZONE_NORMAL = {
    "ZoneID": 1,
    "ZoneDescription": "Normal",
    "ZoneStatus": ZoneStatus.NORMAL,
    "PartitionId": 1,
}

ZONE_LOW_BATTERY = {
    "ZoneID": 1,
    "ZoneDescription": "Low Battery",
    "ZoneTypeId": ZoneType.SECURITY,
    "PartitionId": 1,
    "CanBeBypassed": 1,
    "ZoneStatus": ZoneStatus.LOW_BATTERY,
}

ZONE_INFO = []
ZONE_INFO.append(ZONE_NORMAL)

ZONE_INFO_LOW_BATTERY = []
ZONE_INFO_LOW_BATTERY.append(ZONE_LOW_BATTERY)

ZONES = {"ZoneInfo": ZONE_INFO}
ZONES_LOW_BATTERY = {"ZoneInfo": ZONE_INFO_LOW_BATTERY}
ZS_NORMAL = {
    "PartitionId": 1,
    "Batterylevel": "-1",
    "Signalstrength": "-1",
    "zoneAdditionalInfo": {"DeviceType": "test"},
    "ZoneID": 1,
    "ZoneStatus": ZoneStatus.NORMAL,
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneFlags": None,
}

ZONE_STATUS_LYRIC_CONTACT = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_CONTACT["ZoneTypeId"] = ZoneType.ENTRY_EXIT1

ZONE_STATUS_LYRIC_MOTION = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_MOTION["ZoneTypeId"] = ZoneType.INTERIOR_FOLLOWER

ZONE_STATUS_LYRIC_POLICE = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_POLICE["ZoneTypeId"] = ZoneType.SILENT_24HR

ZONE_STATUS_LYRIC_TEMP = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_TEMP["ZoneTypeId"] = ZoneType.MONITOR

ZONE_STATUS_LYRIC_KEYPAD = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_KEYPAD["ZoneTypeId"] = ZoneType.LYRIC_KEYPAD

ZONE_STATUS_LYRIC_LOCAL_ALARM = ZS_NORMAL.copy()
ZONE_STATUS_LYRIC_LOCAL_ALARM["ZoneTypeId"] = ZoneType.LYRIC_LOCAL_ALARM

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
    "PartitionId": 1,
    "ArmingState": ArmingState.DISARMED.value,
}

PARTITION_DISARMED2 = {
    "PartitionID": "2",
    "ArmingState": ArmingState.DISARMED.value,
}

PARTITION_ARMED_STAY = {
    "PartitionId": 1,
    "ArmingState": ArmingState.ARMED_STAY.value,
}

PARTITION_ARMED_STAY_NIGHT = {
    "PartitionId": 1,
    "ArmingState": ArmingState.ARMED_STAY_NIGHT.value,
}

PARTITION_ARMED_AWAY = {
    "PartitionId": 1,
    "ArmingState": ArmingState.ARMED_AWAY.value,
}

PARTITION_ARMED_STAY_PROA7 = {
    "PartitionID": 1,
    "ArmingState": 10230,
    "PartitionName": "Test_10230",
}

PARTITION_INFO_DISARMED = [PARTITION_DISARMED, PARTITION_DISARMED2]

PARTITION_INFO_ARMED_STAY = [PARTITION_ARMED_STAY]

PARTITION_INFO_ARMED_STAY_NIGHT = [PARTITION_ARMED_STAY_NIGHT]

PARTITION_INFO_ARMED_AWAY = [PARTITION_ARMED_AWAY]

HTTP_PARTITIONS_DISARMED = PARTITION_INFO_DISARMED
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
    "ArmingState": ArmingState.DISARMED.value,
}
RESPONSE_ARMED_STAY = {
    "ResultCode": 0,
    "ResultData": "Success",
    "PanelMetadataAndStatus": METADATA_ARMED_STAY,
    "ArmingState": ArmingState.ARMED_STAY.value,
}
RESPONSE_ARMED_STAY_NIGHT = {
    "ResultCode": 0,
    "PanelMetadataAndStatus": METADATA_ARMED_STAY_NIGHT,
    "ArmingState": ArmingState.ARMED_STAY_NIGHT.value,
}
RESPONSE_ARMED_AWAY = {
    "ResultCode": 0,
    "ResultData": "Success",
    "PanelMetadataAndStatus": METADATA_ARMED_AWAY,
    "ArmingState": ArmingState.ARMED_AWAY.value,
}


RESPONSE_BAD_USER_OR_PASSWORD = {
    "ResultCode": _ResultCode.BAD_USER_OR_PASSWORD.value,
    "ResultData": "testing bad user or password",
}

RESPONSE_DISARM_SUCCESS = {
    "ResultCode": _ResultCode.DISARM_SUCCESS.value,
    "ResultData": "testing disarm success",
}

RESPONSE_INVALID_SESSION = {
    "ResultCode": _ResultCode.INVALID_SESSION.value,
    "ResultData": "testing invalid session",
}

RESPONSE_FAILED_TO_CONNECT = {
    "ResultCode": _ResultCode.FAILED_TO_CONNECT.value,
    "ResultData": "testing failed to connect",
}

RESPONSE_CONNECTION_ERROR = {
    "ResultCode": _ResultCode.CONNECTION_ERROR.value,
    "ResultData": "testing connection error",
}


RESPONSE_SESSION_INITIATED = {
    "ResultCode": _ResultCode.SESSION_INITIATED.value,
    "ResultData": "testing session initiated",
    "SessionID": "54321",
}

RESPONSE_FEATURE_NOT_SUPPORTED = {
    "ResultCode": _ResultCode.FEATURE_NOT_SUPPORTED.value,
    "ResultData": "testing user code feature not supported",
}

RESPONSE_UNKNOWN = {
    "ResultCode": -123456,
    "ResultData": "testing unknown result code",
}

PARTITION_DETAILS_1 = {
    "PartitionID": 1,
    "ArmingState": ArmingState.DISARMED.value,
    "PartitionName": "Test1",
}

PARTITION_DETAILS_2 = {
    "PartitionID": 2,
    "ArmingState": ArmingState.DISARMED.value,
    "PartitionName": "Test2",
}

PARTITION_DETAILS = {"PartitionDetails": [PARTITION_DETAILS_1]}

RESPONSE_PARTITION_DETAILS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "testing partition details",
    "PartitionsInfoList": PARTITION_DETAILS,
}

PARTITION_DETAILS_TWO = {"PartitionDetails": [PARTITION_DETAILS_1, PARTITION_DETAILS_2]}
RESPONSE_PARTITION_DETAILS_TWO = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "testing partition details",
    "PartitionsInfoList": PARTITION_DETAILS_TWO,
}

HTTP_RESPONSE_SESSION_DETAILS = {
    "ResultCode": 0,
    "ResultData": "Success",
    "SessionDetailsResult": {
        "SessionID": "12345",
        "Locations": LOCATIONS,
        "ModuleFlags": MODULE_FLAGS,
        "UserInfo": USER,
    },
}

HTTP_RESPONSE_SESSION_DETAILS_EMPTY = copy.deepcopy(HTTP_RESPONSE_SESSION_DETAILS)
HTTP_RESPONSE_SESSION_DETAILS_EMPTY["SessionDetailsResult"]["Locations"] = None

SESSION_ID = "12345"
TOKEN_EXPIRATION_TIME = 1200
HTTP_RESPONSE_TOKEN = {
    "access_token": jwt.encode({"ids": SESSION_ID}, key="key", algorithm="HS256"),
    "refresh_token": "refresh",
    "expires_in": TOKEN_EXPIRATION_TIME,
}

SESSION_ID_2 = "54321"
HTTP_RESPONSE_TOKEN_2 = {
    "access_token": jwt.encode({"ids": SESSION_ID_2}, key="key", algorithm="HS256"),
    "refresh_token": "refresh2",
    "expires_in": TOKEN_EXPIRATION_TIME,
}

HTTP_RESPONSE_BAD_USER_OR_PASSWORD = {
    "error": _ResultCode.BAD_USER_OR_PASSWORD.value,
    "error_description": "Bad username",
}

HTTP_RESPONSE_REFRESH_TOKEN_FAILED = {"error": "Invalid session"}

HTTP_RESPONSE_PARTITION_DETAILS = {
    "Partitions": [PARTITION_DETAILS_1, PARTITION_DETAILS_2]
}

HTTP_RESPONSE_ZONE_DETAILS = {
    "ZoneStatus": {
        "Zones": ZONE_DETAIL_STATUS,
    }
}

HTTP_RESPONSE_STATUS_DISARMED = {
    "PanelStatus": {
        "Zones": ZONE_INFO,
        "PromptForImportSecuritySettings": False,
        "IsAlarmResponded": False,
        "IsCoverTampered": False,
        "Bell1SupervisionFailure": False,
        "Bell2SupervisionFailure": False,
        "SyncSecDeviceFlag": False,
        "LastUpdatedTimestampTicks": 7,
        "ConfigurationSequenceNumber": 8,
        "IsInACLoss": False,
        "IsInLowBattery": False,
        "IsInRfJam": False,
        "IsInBatteryMissing": False,
        "Partitions": HTTP_PARTITIONS_DISARMED,
    },
    "ArmingState": ArmingState.DISARMED,
    "IsSensorTrippedAlarm": False,
    "IsAlarmResponded": False,
    "IsCoverTampered": False,
    "Bell1SupervisionFailure": False,
    "Bell2SupervisionFailure": False,
}

################################################ NEW TEST DATA ##########################################

HTTP_RESPONSE_CONFIG = {
    "RevisionNumber": "1.2.3",
    "version": "0.0.4",
    "AppConfig": [
        {
            "tc2APIKey": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6bdkwTazBVt7eIcelDFcfojTC4XwDAfmvVJq9EdjyCa7neeow4tfoWe57oLPkjw+Ge5VEgUOus7aqhywKBTwlmlGUiTpQLUtVuxmam2nG3kvbKA2T6HbWKQfrJsdGitZLgwOIfzjDrIFTUjRiTIV8CYO8rmsLtaQUE20PRGNvesYP1tb7e4wqdGX3J6je/bpbNRwglnarzIEw37JjCsnhZi9iaUOWbHrvrb98MsLqyugvOtCwt/NGntZ8JJeFHLMHpuHu6uM2H+wotvwE1zSNL4+DScp/vpc4Cc55rksIOaOTB8F2OhxpTnlPzcVs6Av8HYEKyrWl4vSAqS5OcIPkQIDAQAB",
            "tc2ClientId": "9fcfbf759b0b4e5c83cd03cea1d20d59",
        }
    ],
    "brandInfo": [
        {
            "AppID": 16808,
            "BrandName": "totalconnect",
        },
    ],
}


"""
Below are real results from a ProA7Plus panel
LocationID and similar have been replaced with fake numbers
"""

LOCATION_ID = 1234567
LOCATION_NAME = "Test Location"
SECURITY_DEVICE_ID = 7654321
USER_ID = 9876543


REST_RESULT_SESSION_DETAILS = {
    "SessionDetailsResult": {
        "ModuleFlags": "Security=1,Video=1,Automation=1,GPS=1,VideoPIR=1,ReadState=1,IsAlexaEnabled=0,SPAEnabled=0,ShowPrivacyLink=0",
        "SessionID": "70F12813-0ABC-4634-AAE0-E56B342E6A21",
        "PrivacyStatementUrl": "https://www.resideo.com/us/en/corporate/legal/eula/english-us/#_PRIVACY_RESIDEO",
        "UserInfo": {
            "UserID": USER_ID,
            "Username": "test_user",
            "Fullname": "Test User",
            "Language": 0,
            "LocaleID": 0,
            "UserFeatureList": "Master=0,User Administration=0,Configuration Administration=0",
            "ClientPreferences": "",
            "IsEulaAccepted": True,
            "IsSMSEulaAccepted": False,
            "DateFormatID": 0,
            "TimeFormatID": 0,
            "PushNotificationStatus": 0,
            "HasResetPassword": True,
            "IsRootedDeviceAccepted": False,
            "IsLocalyticsEnabled": -1,
            "IsAppStoreLogEnabled": -1,
            "IsMarketingOptionEnabled": 1,
            "IsMarketingDefaultValue": 1,
            "IsMonitoringDefaultValue": -1,
            "IsOtpSupported": 1,
            "IsOtpEnabled": 0,
            "UserOtpEmail": None,
            "ForceResetPassword": False,
            "UserCodeDirectPushEnabled": False,
        },
        "Locations": [
            {
                "LocationID": LOCATION_ID,
                "LocationName": LOCATION_NAME,
                "PhotoURL": "",
                "LocationModuleFlags": "Security=1,Video=0,Automation=0,GPS=0,VideoPIR=0,TimeTriggeredEvent=0,TemperatureUnits=F,ConfigureContent=1,SyncLocation=0,ConfigureSlideshow=0,TimezoneOffset=-8.0,SmartAction=1,CustomArm=0,NoTriggerScene=1,NoScene=1,AutoSyncEnabled=1,WiFIThermostatEnabled=1,SupportsOnlyHDPhotos=1,SyncStatusSupported=1,WiFiHBSupported=1,DoorBellSupported=1,masterUserCodeSync=0,GeofenceStatus=0,RSISupported=0,VideoServiceEnabled=0,HasAddressUpdated=1,WifiGaragedoorSupported=0,OutboundServiceEnabled=0,HasSmartScenes=0,MotionViewerServiceEnabled=0,VavEnabled=0,UserManagementDisabled=0,HomeCardUpdatedTimestamp=1/1/1900 12:00:00 AM,CameraPartitionFTUE=True,PostalCodeType=NA,IsGoogleHomeSupported=True,SmsCarrierEnabled=True,IsEMEALocation=0,EdimaxServiceDisabled=True,UnicornSupported=0,IsManageDevicesSupported=True,IsAlexaSupported=False,MonitoringType=-1,SmartActionConfigEnabled=0",
                "SecurityDeviceID": SECURITY_DEVICE_ID,
                "LocationInfoSimple": {
                    "LocationId": LOCATION_ID,
                    "LocationName": LOCATION_NAME,
                    "AccountId": 12345678901,
                    "PhotoId": -1,
                    "TimeZoneId": 7,
                    "PhotoURL": "",
                    "SetDefaultLocationName": False,
                    "SecuritySystemAlias": "",
                    "SecuritySystemPanelDeviceID": SECURITY_DEVICE_ID,
                    "CountryID": 1,
                    "StreetNumber": "",
                    "StreetName": "123 Main Street",
                    "City": "Some Town",
                    "StateID": 5,
                    "PostalCode": "99999",
                    "TemperatureUnits": "F",
                    "Latitude": None,
                    "Longitude": None,
                },
                "PanelConnectionStatusInfo": [
                    {
                        "LocationID": LOCATION_ID,
                        "LocationName": LOCATION_NAME,
                        "PhotoURL": "",
                        "ConnectionStatus": 1,
                        "SyncStatus": 1,
                        "SyncStatusMessage": "",
                        "ConnectionType": 0,
                        "SingnalStrength": None,
                    }
                ],
                "DeviceList": [
                    {
                        "DeviceID": SECURITY_DEVICE_ID,
                        "DeviceName": "Security System",
                        "DeviceClassID": 1,
                        "DeviceSerialNumber": "1234567890AB",
                        "DeviceFlags": "PromptForUserCode=0,PromptForInstallerCode=0,PromptForImportSecuritySettings=0,AllowUserSlotEditing=0,CalCapable=1,CanBeSentToPanel=1,CanArmNightStay=0,CanSupportMultiPartition=0,PartitionCount=0,MaxPartitionCount=4,OnBoardingSupport=0,PartitionAdded=0,DuplicateUserSyncStatus=0,PanelType=12,PanelVariant=1,BLEDisarmCapable=0,ArmHomeSupported=1,DuplicateUserCodeCheck=1,CanSupportRapid=0,IsKeypadSupported=0,WifiEnrollmentSupported=1,IsConnectedPanel=1,ArmNightInSceneSupported=1,BuiltInCameraSettingsSupported=0,ZWaveThermostatScheduleDisabled=0,MultipleAuthorityLevelSupported=1,VideoOnPanelSupported=1,EnableBLEMode=0,IsPanelWiFiResetSupported=0,IsCompetitorClearBypass=0,IsNotReadyStateSupported=0,isArmStatusWithoutExitDelayNotSupported=0,UserCodeLength=4,UserCodeLengthChanged=0,DoubleDisarmRequired=0,TMSCloudSupported=0,IsAVCEnabled=0",
                        "SecurityPanelTypeID": 12,
                        "DeviceSerialText": None,
                        "DeviceType": None,
                        "DeviceVariants": None,
                        "RestrictedPanel": 0,
                    },
                    {
                        "DeviceID": 6123456,
                        "DeviceName": "Built-In Camera",
                        "DeviceClassID": 6,
                        "DeviceSerialNumber": "2345678901AB",
                        "DeviceFlags": "",
                        "SecurityPanelTypeID": 0,
                        "DeviceSerialText": None,
                        "DeviceType": None,
                        "DeviceVariants": None,
                        "RestrictedPanel": 0,
                    },
                    {
                        "DeviceID": 7123456,
                        "DeviceName": "Front Door",
                        "DeviceClassID": 7,
                        "DeviceSerialNumber": "001234567890",
                        "DeviceFlags": "",
                        "SecurityPanelTypeID": 0,
                        "DeviceSerialText": None,
                        "DeviceType": None,
                        "DeviceVariants": None,
                        "RestrictedPanel": 0,
                    },
                ],
            }
        ],
    },
    "ResultCode": 0,
    "ResultData": "Success",
}

REST_RESULT_PARTITIONS_CONFIG = {
    "Partitions": [
        {
            "PartitionName": "Partition-01",
            "IsStayArmed": False,
            "IsFireEnabled": False,
            "IsCommonEnabled": False,
            "IsLocked": False,
            "IsNewPartition": False,
            "IsNightStayEnabled": 0,
            "ExitDelayTimer": 0,
            "PartitionID": 1,
            "PartitionArmingState": 10214,
            "ArmingState": 10214,
            "OverrideArmingState": 0,
            "OverrideTimeStamp": None,
            "IsAlarmResponded": False,
            "AlarmTriggerTime": None,
            "AlarmTriggerTimeLocalized": None,
        }
    ]
}

REST_RESULT_PARTITIONS_ZONES = {
    "ZoneStatus": {
        "Zones": [
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "020000",
                    "LoopNumber": 1,
                    "ResponseType": "1",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 2,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 1,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "030000",
                    "LoopNumber": 1,
                    "ResponseType": "4",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 2,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 3,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 4,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "040000",
                    "LoopNumber": 1,
                    "ResponseType": "4",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 2,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 4,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 4,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "050000",
                    "LoopNumber": 1,
                    "ResponseType": "4",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 2,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 5,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 4,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "060000",
                    "LoopNumber": 1,
                    "ResponseType": "1",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 1,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 6,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 1,
            },
            {
                "PartitionId": 1,
                "Batterylevel": 5,
                "Signalstrength": 2,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "070000000000000A",
                    "LoopNumber": 2,
                    "ResponseType": "53",
                    "AlarmReportState": 0,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 15,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 7,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 53,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "080000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 8,
                "ZoneStatus": 1,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "090000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 9,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "100000",
                    "LoopNumber": 1,
                    "ResponseType": "1",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 10,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 1,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "120000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 12,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "130000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 13,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "140000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 1,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 14,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "150000",
                    "LoopNumber": 1,
                    "ResponseType": "3",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 1,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 15,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 3,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "160000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 16,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "170000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 17,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "180000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 18,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "190000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 19,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "200000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 20,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "210000",
                    "LoopNumber": 1,
                    "ResponseType": "14",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 6,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 21,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 14,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "220000",
                    "LoopNumber": 1,
                    "ResponseType": "14",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 6,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 22,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 14,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "230000",
                    "LoopNumber": 1,
                    "ResponseType": "14",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 6,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 23,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 14,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "240000",
                    "LoopNumber": 1,
                    "ResponseType": "9",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 4,
                },
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 24,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": 5,
                "Signalstrength": 3,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "250000000000000A",
                    "LoopNumber": 1,
                    "ResponseType": "23",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 0,
                    "DeviceType": 15,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 25,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 23,
            },
            {
                "PartitionId": 1,
                "Batterylevel": 5,
                "Signalstrength": 5,
                "zoneAdditionalInfo": {
                    "SensorSerialNumber": "260000000000000A",
                    "LoopNumber": 1,
                    "ResponseType": "1",
                    "AlarmReportState": 1,
                    "ZoneSupervisionType": 0,
                    "ChimeState": 1,
                    "DeviceType": 0,
                },
                "CanBeBypassed": 1,
                "ZoneFlags": None,
                "ZoneID": 26,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 1,
                "ZoneTypeId": 1,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": None,
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 800,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 0,
                "ZoneTypeId": 50,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": None,
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 1995,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 0,
                "ZoneTypeId": 9,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": None,
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 1996,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 0,
                "ZoneTypeId": 15,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": None,
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 1998,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 0,
                "ZoneTypeId": 6,
            },
            {
                "PartitionId": 1,
                "Batterylevel": -1,
                "Signalstrength": -1,
                "zoneAdditionalInfo": None,
                "CanBeBypassed": 0,
                "ZoneFlags": None,
                "ZoneID": 1999,
                "ZoneStatus": 0,
                "IsBypassableZone": 0,
                "IsSensingZone": 0,
                "ZoneTypeId": 7,
            },
        ]
    }
}

REST_RESULT_FULL_STATUS = {
    "PanelStatus": {
        "Zones": [
            {
                "ZoneID": 8,
                "ZoneDescription": "Office Side Door",
                "ZoneStatus": 1,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 0,
            },
            {
                "ZoneID": 2,
                "ZoneDescription": "Kitchen  Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-12-11T09:00:13",
                "ZoneTypeID": 1,
                "DeviceType": 0,
            },
            {
                "ZoneID": 3,
                "ZoneDescription": "Living Room  Motion Sensor",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-06-02T15:41:05",
                "ZoneTypeID": 4,
                "DeviceType": 2,
            },
            {
                "ZoneID": 4,
                "ZoneDescription": "Hallway  Motion Sensor",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-12-11T09:00:13",
                "ZoneTypeID": 4,
                "DeviceType": 2,
            },
            {
                "ZoneID": 5,
                "ZoneDescription": "Master Bedroom  Motion Sensor",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-06-02T15:40:59",
                "ZoneTypeID": 4,
                "DeviceType": 2,
            },
            {
                "ZoneID": 6,
                "ZoneDescription": "Garage  Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 1,
                "DeviceType": 0,
            },
            {
                "ZoneID": 7,
                "ZoneDescription": "Doorbell  Other",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 53,
                "DeviceType": 15,
            },
            {
                "ZoneID": 9,
                "ZoneDescription": "Office Back Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 0,
            },
            {
                "ZoneID": 10,
                "ZoneDescription": "Master Bedroom  Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-06-02T15:40:57",
                "ZoneTypeID": 1,
                "DeviceType": 0,
            },
            {
                "ZoneID": 12,
                "ZoneDescription": "Dining Room Two Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 0,
            },
            {
                "ZoneID": 13,
                "ZoneDescription": "Patio  Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 0,
            },
            {
                "ZoneID": 14,
                "ZoneDescription": "Living Room  Window",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 1,
            },
            {
                "ZoneID": 15,
                "ZoneDescription": "Living Room Two Window",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 3,
                "DeviceType": 1,
            },
            {
                "ZoneID": 16,
                "ZoneDescription": "Apartment  SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:42:29",
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 17,
                "ZoneDescription": "Upstairs Hallway SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:53:57",
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 18,
                "ZoneDescription": "Downstairs Hallway SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:47:10",
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 19,
                "ZoneDescription": "Kid Bedroom SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:49:07",
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 20,
                "ZoneDescription": "Guest Bedroom SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:50:20",
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 21,
                "ZoneDescription": "Apartment  CarbonMonoxideDetecto",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:41:18",
                "ZoneTypeID": 14,
                "DeviceType": 6,
            },
            {
                "ZoneID": 22,
                "ZoneDescription": "Downstairs Hallway CarbonMonoxid",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:45:39",
                "ZoneTypeID": 14,
                "DeviceType": 6,
            },
            {
                "ZoneID": 23,
                "ZoneDescription": "Upstairs Hallway CarbonMonoxideD",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-04-28T09:52:37",
                "ZoneTypeID": 14,
                "DeviceType": 6,
            },
            {
                "ZoneID": 24,
                "ZoneDescription": "Master Bedroom  SmokeDetector",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 9,
                "DeviceType": 4,
            },
            {
                "ZoneID": 25,
                "ZoneDescription": "Garage Side  Other",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": "2024-12-15T15:14:39",
                "ZoneTypeID": 23,
                "DeviceType": 15,
            },
            {
                "ZoneID": 26,
                "ZoneDescription": "Front Door  Door",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 1,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 1,
                "DeviceType": 0,
            },
            {
                "ZoneID": 800,
                "ZoneDescription": "Master Bedroom Keypad",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 50,
                "DeviceType": 0,
            },
            {
                "ZoneID": 1995,
                "ZoneDescription": "Zone 995 Fire",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 9,
                "DeviceType": 11,
            },
            {
                "ZoneID": 1996,
                "ZoneDescription": "Zone 996 Medical",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 15,
                "DeviceType": 10,
            },
            {
                "ZoneID": 1998,
                "ZoneDescription": "Zone 998 Other",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 6,
                "DeviceType": 15,
            },
            {
                "ZoneID": 1999,
                "ZoneDescription": "Zone 999 Police",
                "ZoneStatus": 0,
                "PartitionID": 1,
                "CanBeBypassed": 0,
                "AlarmTriggerTime": None,
                "AlarmTriggerTimeLocalized": None,
                "ZoneTypeID": 7,
                "DeviceType": 12,
            },
        ],
        "PromptForImportSecuritySettings": False,
        "IsAlarmResponded": False,
        "IsCoverTampered": False,
        "Bell1SupervisionFailure": False,
        "Bell2SupervisionFailure": False,
        "SyncSecDeviceFlag": False,
        "LastUpdatedTimestampTicks": 638746327230000000,
        "ConfigurationSequenceNumber": 72,
        "IsInACLoss": False,
        "IsInLowBattery": False,
        "IsInRfJam": False,
        "IsInBatteryMissing": False,
        "Partitions": [
            {
                "PartitionName": "",
                "IsStayArmed": False,
                "IsFireEnabled": False,
                "IsCommonEnabled": False,
                "IsLocked": False,
                "IsNewPartition": False,
                "IsNightStayEnabled": 0,
                "ExitDelayTimer": 0,
                "PartitionID": 1,
                "PartitionArmingState": 10214,
                "ArmingState": 10214,
                "OverrideArmingState": 0,
                "OverrideTimeStamp": None,
                "IsAlarmResponded": False,
                "AlarmTriggerTime": "2024-12-15T23:15:30",
                "AlarmTriggerTimeLocalized": "2024-12-15T15:15:30",
            }
        ],
    },
    "ArmingState": 10214,
    "IsSensorTrippedAlarm": False,
    "IsAlarmResponded": False,
    "IsCoverTampered": False,
    "Bell1SupervisionFailure": False,
    "Bell2SupervisionFailure": False,
}

REST_RESULT_SECURITY_SYNCHRONIZE = {
    "JobID": "9d085f67-1234-5678-beac-4237a8b7ce8b",
    "ResultCode": 0,
    "ResultData": "Success",
}

REST_RESULT_VALIDATE_USER_LOCATIONS = {"IsDuplicate": True}

REST_RESULT_CLEAR_BYPASS = {"ResultCode": 0, "ResultData": "Success"}

REST_RESULT_LOGOUT = {"ResultCode": 0, "ResultData": "Success"}


def panel_with_status(state: ArmingState):
    """Return panel fullStatus result with given arming state."""
    RESULT = copy.deepcopy(REST_RESULT_FULL_STATUS)
    RESULT["ArmingState"] = state.value
    RESULT["PanelStatus"]["Partitions"][0]["PartitionArmingState"] = state.value
    RESULT["PanelStatus"]["Partitions"][0]["ArmingState"] = state.value
    return RESULT


# define various fullStatus results for common tests
PANEL_STATUS_DISARMED = panel_with_status(ArmingState.DISARMED)
PANEL_STATUS_ARMED_AWAY = panel_with_status(ArmingState.ARMED_AWAY)
PANEL_STATUS_ARMED_STAY = panel_with_status(ArmingState.ARMED_STAY)

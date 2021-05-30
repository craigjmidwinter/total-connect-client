"""Test TotalConnectDevice."""

from device import TotalConnectDevice

DEVICE_FULL = {
    "DeviceID": 1234567,
    "DeviceName": "test",
    "DeviceClassID": 1,
    "DeviceSerialNumber": "987654321ABC",
    "DeviceFlags": "PromptForUserCode=0,PromptForInstallerCode=0,PromptForImportSecuritySettings=0,AllowUserSlotEditing=0,CalCapable=1,CanBeSentToPanel=0,CanArmNightStay=0,CanSupportMultiPartition=0,PartitionCount=0,MaxPartitionCount=0,OnBoardingSupport=0,PartitionAdded=0,DuplicateUserSyncStatus=0,PanelType=8,PanelVariant=1,BLEDisarmCapable=0,ArmHomeSupported=0,DuplicateUserCodeCheck=1,CanSupportRapid=0,IsKeypadSupported=1,WifiEnrollmentSupported=0,IsConnectedPanel=0,ArmNightInSceneSupported=0,BuiltInCameraSettingsSupported=0,ZWaveThermostatScheduleDisabled=0,MultipleAuthorityLevelSupported=0,VideoOnPanelSupported=0,EnableBLEMode=0,IsPanelWiFiResetSupported=0,IsCompetitorClearBypass=0,IsNotReadyStateSupported=0,isArmStatusWithoutExitDelayNotSupported=0",
    "SecurityPanelTypeID": None,
    "DeviceSerialText": None,
}

def tests_init():
    """Test __init__()."""
    test_device = TotalConnectDevice(DEVICE_FULL)
    assert test_device.id == DEVICE_FULL["DeviceID"]

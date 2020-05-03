# Result Code information

Information on ResultCodes returned from Total Connect.

ResultCode | ResultData | Notes
------------ | - | - 
4500 | ARM_SUCCESS |
4500 | DISARM_SUCCESS | 
4101 | CONNECTION_ERROR | We are unable to connect to the security panel. Please try again later or contact support
0 | SUCCESS | 
-100 | Authentication failed
-102 | INVALID_SESSION |  
-120 | Feature Not Supported | When calling get_zone_details()
-4002 | The specified location is not valid |
-4007 | NoAutomationDeviceFoundAtSpecifiedLocationException |
-4502 | Command failed. Please try again. | Trying to arm system with zone faulted. 
-4104 | Failed to Connect with Security System | 
-4114 | System User Code not available/invalid in Database | https://github.com/craigjmidwinter/total-connect-client/issues/36
-4504 | Failed to Bypass Zone | Happens when requesting to bypass a non-existent zone.
-9001 | Authorization Failed to Perform Notification Configuration | Received when trying getAllSensorsMaskStatus
-10026 | Unable to load your scenes, please try syncing your panel in the Locations menu.  If your panel is still not connecting, please contact your Security Dealer for support | 
-12104 | Automation - We are unable to load your automation devices, please try again or contact your security dealer for support | GetAutomationDeviceStatus with location module flag Automation = 0
-50004 | Input validation failed - Parameter - {0} | Bad username and password provided

Zone Bypass returns SUCCESS even if the zone was in bypass state prior to the request.

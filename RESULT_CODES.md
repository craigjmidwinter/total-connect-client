# Result Code information

Information on ResultCodes returned from Total Connect.

ResultCode | ResultData | Notes
------------ | - | - 
4500 | ARM_SUCCESS |
4500 | DISARM_SUCCESS | 
4101 | CONNECTION_ERROR | We are unable to connect to the security panel. Please try again later or contact support
0 | SUCCESS | 
-102 | INVALID_SESSION |  
-4002 | The specified location is not valid |
-4007 | NoAutomationDeviceFoundAtSpecifiedLocationException | 
-4104 | Failed to Connect with Security System | 
-4114 | System User Code not available/invalid in Database | https://github.com/craigjmidwinter/total-connect-client/issues/36
-4504 | Failed to Bypass Zone | Happens when requesting to bypass a non-existent zone.
-9001 | Authorization Failed to Perform Notification Configuration | Received when trying getAllSensorsMaskStatus
-10026 | Unable to load your scenes, please try syncing your panel in the Locations menu.  If your panel is still not connecting, please contact your Security Dealer for support | 


Zone Bypass returns SUCCESS even if the zone was in bypass state prior to the request.
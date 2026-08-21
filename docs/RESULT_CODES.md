# Result Code information

**Mode:** Reference (empirical). Resideo does not publish a `ResultCode`
catalogue. Every row below was recovered by testing against real
TotalConnect accounts and panels, or reported by users in linked GitHub
issues — not from vendor documentation. Treat "Notes" as the best
explanation available, not a guarantee; the same numeric code has been
observed meaning slightly different things on different panels.

**How to read this table:** every TotalConnect API response carries a
`ResultCode` (and often a matching `ResultData` string). This library's
`total_connect_client.const._ResultCode` enum and
`TotalConnectClient.raise_for_resultcode()` turn a subset of these into
specific exceptions — see
[`api-reference.md`'s exceptions section](api-reference.md#exceptions) for
that mapping. If you're debugging a raw response body and see a `ResultCode`
you don't recognize, look it up here first.

**Worked example** — if `location.arm(ArmType.AWAY)` raises
`BadResultCodeError`, look at the underlying response:

```python
from total_connect_client.exceptions import BadResultCodeError

try:
    location.arm(ArmType.AWAY)
except BadResultCodeError as err:
    response = err.args[1]  # the response dict passed when the exception was raised
    print(response["ResultCode"], response.get("ResultData"))
    # -4502 Command failed. Please try again.
    # -> matches the -4502 row below: "is a zone faulted?"
```

ResultCode | ResultData | Notes
------------ | - | - 
4500 | ARM_SUCCESS |
4500 | DISARM_SUCCESS | 
4500 | SESSION_INITIATED | Session Initiated. Poll for command state update.
4101 | CONNECTION_ERROR | We are unable to connect to the security panel. Please try again later or contact support
0 | SUCCESS | 
-100 | Authentication failed
-102 | INVALID_SESSION |  
-120 | Feature Not Supported | When calling get_zone_details()
-400 | Object reference not set to an instance of an object. | GetPanelMetaDataAndFullStatusEx_V2 without partition list. Also see issue #184
-999 |  Unknown Error | [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)
-4002 | The specified location is not valid |
-4004 | The specified device id is invalid for the current context | [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)
-4007 | NoAutomationDeviceFoundAtSpecifiedLocationException |
-4502 | Command failed. Please try again. | Trying to arm system with zone faulted. 
-4104 | Failed to Connect with Security System | 
-4106 | Invalid user code. Please try again. | When disarming.  https://github.com/craigjmidwinter/total-connect-client/issues/85
-4114 | System User Code not available/invalid in Database | https://github.com/craigjmidwinter/total-connect-client/issues/36 Also happens attempting a code for an incorrect location/device.
-4504 | Failed to Bypass Zone | Happens when requesting to bypass a non-existent zone, or when trying to bypass a zone than cannot be bypassed (i.e. smoke detector).
-7606 | Input Failure | [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)
-7625 | Your email address or password is invalid. Please try again | [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)
-8029 | Your SkyBell HD is offline or not connected to the internet. Please check your SkyBell and try again
-9001 | Authorization Failed to Perform Notification Configuration | Received when trying getAllSensorsMaskStatus
-10026 | Unable to load your scenes, please try syncing your panel in the Locations menu.  If your panel is still not connecting, please contact your Security Dealer for support | 
-12104 | Automation - We are unable to load your automation devices, please try again or contact your security dealer for support | GetAutomationDeviceStatus with location module flag Automation = 0
-15003 | RSI : No Device Available| [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)
-16000 | InvalidDeviceID | [#213](https://github.com/craigjmidwinter/total-connect-client/issues/213)  requesting wiFiDoorBellDiagnosticInfo with a non-doorbell device ID
-50004 | Input validation failed - Parameter - {0} | Bad username and password provided

Zone Bypass returns SUCCESS even if the zone was in bypass state prior to the request.

# Notes from early development with the new REST API

## General notes

Watch the HTTP type (GET, PUT, etc) in the request and ensure the request parameters are in the right place.  For GET use `params` but for POST use `data`.

For many calls, while the userCode (or UserCode or usercode) is marked as optional, the call fails without it.

## Result Codes

Not all API calls provide a ResultCode. It seems to be if there is no ResultCode and no error, then there was success.

However, some calls like disArm provide:

```txt
Message: 'Received HTTP error code 500 with response:'
Arguments: (b'{"Message":"Request Not Completed, Please Try Again Later"}',)
```

This seems to be when it doesn't make sense to actually do the action requested.  For example, this response is provided when asking to disarm an already disarmed panel.

```txt
DEBUG:urllib3.connectionpool:https://rs.alarmnet.com:443 "PUT /TC2API.TCResource/api/v1/locations/123/devices/456/bypass?ZoneIds=8 HTTP/11" 500 48
DEBUG:total_connect_client.client:response:
	ok: False
	raw:
<Response [500]>
	json:
{'ResultCode': -999, 'ResultData': 'Unknown Error'}
```

## Get Zone Details

Fails the first time, every time (since I noticed and have been watching).  Works the second time (first re-try) every time.
```txt
DEBUG:urllib3.connectionpool:https://rs.alarmnet.com:443 "GET /TC2API.TCResource/api/v1/locations/123/partitions/zones/0 HTTP/11" 200 None
DEBUG:total_connect_client.client:response:
	ok: True
	raw:
<Response [200]>
	json:
{'ResultCode': 4101, 'ResultData': 'We are unable to connect to the security panel. Please try again later or contact support'}
```
# Other Random Stuff

Request: https://rs.alarmnet.com/TC2API.TCResource/api/v1/notificationLists
Response: 
```json
{'NotificationListCollection': [{'NotificationListID': 4444444, 'NotificationListName': 'Default Group', 'IsNotificationListEnabled': True, 'IsInUse': True, 'AssociatedUsers': [{'UserID': 9876543}]}, {'NotificationListID': 33333333, 'NotificationListName': 'DoorBell Events', 'IsNotificationListEnabled': True, 'IsInUse': True, 'AssociatedUsers': [{'UserID': 9876543}]}], 'ResultCode': 0, 'ResultData': 'Success'}
```

# Probably unchanging stuff ?
I don't think any of these results will change on a regular basis

Request: https://rs.alarmnet.com/TC2API.TCResource/api/v1/account/notificationMethods
Response: 
```json
{'NotificationMethods': [{'NotificationMethodID': 0, 'NotificationMethodName': 'None'}, {'NotificationMethodID': 1, 'NotificationMethodName': 'Short Text Email (SMS)'}, {'NotificationMethodID': 2, 'NotificationMethodName': 'Text Email'}, {'NotificationMethodID': 3, 'NotificationMethodName': 'HTML Email'}, {'NotificationMethodID': 4, 'NotificationMethodName': 'Text Email with Attachment(s)'}, {'NotificationMethodID': 5, 'NotificationMethodName': 'HTML Email with Attachment(s)'}, {'NotificationMethodID': 6, 'NotificationMethodName': 'PureSms'}, {'NotificationMethodID': 7, 'NotificationMethodName': 'Push Notification'}], 'ResultCode': 0, 'ResultData': 'Success'}
```

Request: https://rs.alarmnet.com/TC2API.TCResource/api/v1/services/version
Response: 
```json
{'ResultCode': 0, 'ResultData': 'TC2 API Version 6.26.1.41'}
```

Request: https://rs.alarmnet.com/TC2API.TCResource/api/v2/interfaceSchema/clientId/16808/clientAppVersion?appVersion=3.41.1.71
Response: 
```json
{'InterfaceSchemaConfigInfo': {'AppleDownloadURL': '', 'AndroidDownloadURL': '', 'LatestSupportedAppVersion': '', 'Whatsnew': '', 'SignalrHubUrl': 'https://rs.alarmnet.com/TC2HubService/SignalRHub', 'GatewayUrl': 'https://rs.alarmnet.com/TC2ApiGateway'}, 'ResultCode': 0, 'ResultData': 'Success'}
```

Request: https://rs.alarmnet.com/TC2API.TCResource/api/Dashboard
Response: 
```json
{'systemStatus': [{'ServiceId': 1, 'ServiceName': 'Alarm Monitoring', 'Status': 'GOOD', 'Description': 'OPERATIONAL'}, {'ServiceId': 2, 'ServiceName': 'Total Connect', 'Status': 'GOOD', 'Description': 'OPERATIONAL'}, {'ServiceId': 3, 'ServiceName': 'Total Connect Video', 'Status': 'GOOD', 'Description': 'OPERATIONAL'}], 'ResultCode': 0, 'ResultData': 'Success'}
```

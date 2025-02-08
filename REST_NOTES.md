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

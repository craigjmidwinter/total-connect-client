# Total-Connect-Client
Total-Connect-Client is a super simple python client for interacting with TotalConnect2 alarm system.

Started by @craigjmidwinter to add alarm support for his personal HomeAssistant set-up, with later contributions from others.

The code currently supports:
 - Arming (away, stay, night)
 - Disarming
 - Getting panel status (armed, bypassed, etc)
 - Getting zone status (normal, fault, trouble, low battery, etc)

## Troubleshooting

If you're having trouble with your system, or find an error message, we may ask you to submit information about your alarm system.  To do that from the command line do the following steps (assuming you are running from within Home Assistant):
 
First download the latest files:
 - `wget https://raw.githubusercontent.com/craigjmidwinter/total-connect-client/master/total_connect_client/TotalConnectClient.py`
 - `wget https://raw.githubusercontent.com/craigjmidwinter/total-connect-client/master/total_connect_client/info.py`
 
The run the script:
 - A usercode is not required for most systems.  Enter '-1' in it's place unless you need to enter your panel code.
 - `python3 info.py username password usercode`  
 
If you want to easily put the info into a file for sharing: 
 - `python3 info.py username password usercode > my_info.txt`
 - Now the file my_info.txt in the same directory will hold all of that information

**WARNING**:  the script will include private information including your username and password.  Carefully remove it before sharing with the developers or posting on Github.

Create an Issue on Github and post both your problem and your system information.

Why do we ask for this information?  The TotalConnect API documentation provides little information on the status codes and other information it returns about your system.  We developed as best we could using the codes our own systems returned.  We have seen many times that other users with issues have different system status codes.
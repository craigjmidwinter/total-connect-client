# Total-Connect-Client

Total-Connect-Client is a python client for interacting with the [TotalConnect2](https://totalconnect2.com) alarm system.

Started by @craigjmidwinter to add alarm support for his personal HomeAssistant set-up, with later contributions from others.

To use with Home Assistant, follow the instructions to set up [Total Connect](https://www.home-assistant.io/integrations/totalconnect/).

For command line or other uses, the package can be downloaded at [PyPI](https://pypi.org/project/total-connect-client/).

The code currently supports:

- Arming (away, stay, night)
- Disarming
- Getting panel status (armed, bypassed, etc)
- Getting zone status (normal, fault, trouble, low battery, etc)

## Zone Status

To see zones that are faulted (open), your Total Connect account must have “Sensor Activities” enabled. Your alarm monitoring company may charge an extra fee to enable this. If available, these can be found in the Total Connect 2 web portal at **Notifications -> Sensor Activities**. Alternately, they can be found in the Total Connect mobile app at **More -> Settings -> Notifications -> Sensor Activities**.

## Troubleshooting

If you're having trouble with your system, or find an error message, we may ask you to submit information about your alarm system.

First look at the [Total Connect system status](https://status.resideo.com/) to see if there is a system wide problem.

### Internet connection

Total Connect depends on the network connection between your alarm and the Total Connect server, and the connection between your client (your Home Assistant) and the Total Connect server.

Check your internet connection to make sure your alarm and your client are connected to the internet.

### From Home Assistant

- Go to https://<your_home_assistant>/config/integrations
- Find the TotalConnect integration card and click on the three dots in the bottom right corner
- Click on Download Diagnostics

If you're not able to to download the diagnostics file for some reason, use the Command Line instructions below.

### From the command line

Do the following steps from any computer with a current version of Python installed. It does not have to be from the computer hosting your Home Assistant.

```command-line
pip install total-connect-client
python3 -m total_connect_client username
```

If you want to easily put the info into a file for sharing:

- `python3 -m total_connect_client username > my_info.txt`
- Now the file my_info.txt in the same directory will hold all of that information

**WARNING**: the output of this command includes private information including your username and password. Carefully remove it before sharing with the developers or posting on Github.

Create an Issue on Github and post both your problem and your system information.

Why do we ask for this information? The TotalConnect API documentation provides little information on the status codes and other information it returns about your system. We developed as best we could using the codes our own systems returned. We have seen many times that other users with issues have different system status codes.

## Developers

If you're a developer and want to interface to TotalConnect from a system other than Home Assistant, see the [developer docs](docs/DEVELOPER.md).

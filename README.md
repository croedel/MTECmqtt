# M-TEC Modbus API
Welcome to the `M-TEC Modbus API` project!

This is actually my second approach to read data from a M-TEC Energybutler (https://www.mtec-systems.com) system.
My first approach was to use the Web-portal - you can find the outcome at my project `M-TEC API`.

After more research, I am now happy to present my second approach!

The highlights are:
* No additional hardware or modifications of your Inverter required
* Uses standard Modbus communication protocol
* Enables to read out more than 70 parameters from your Inverter
* Works within you LAN - no internet connection required
* Enables fast polling of essential data (e.g. every 10s)
* Data can be exported as CSV or can be send to a MQTT broker, enabling an easy integration into almost any EMS or home automation tool.

## Remarks 
In order not to do uninteneded changes or settings and avoid any side-effects, I intentionally implemented read functionality only. 

This project would not have been possible without the really valuable pre-work of other people: 
* https://www.photovoltaikforum.com/thread/206243-erfahrungen-mit-m-tec-energy-butler-hybrid-wechselrichter
* https://forum.iobroker.net/assets/uploads/files/1681811699113-20221125_mtec-energybutler_modbus_rtu_protkoll.pdf
* https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol

_Disclaimer:_ This project is a pure hobby project which I created by reverse-engineering the M-TEC Web-portal. It is *not* related to or supported by M-TEC GmbH by any means. Usage is on you own risk. I don't take any responsibility on functionality or potential damage.


## What it offers
### API
The actual API can be found in `MTECmodbusAPI.py`. It offers functionality to:
* Connect to the Modbus server of your inverter 
* Retrieve current status and usage data

### Commandline tool
The command-line tool `MTEC_tool.py` offers functionality to export all known parameters.

### MQTT server
The MQTT server `MTEC_modbus_mqtt.py` enables to export data to a MQTT broker. This can be useful, if you want to use the data e.g. as source for an EMS or home automation tool. Many of them enable to read data from MQTT, therefore this might be a good option for an easy integration.


## Setup & configuration
As prerequisites, you need to have installed: 
* Python 3 
* PyYAML https://pypi.org/project/PyYAML/
* PyModbus https://pymodbus.readthedocs.io/en/latest/

(Depending on your Python installation, installation might require root rights or using `sudo`)

PyYAML and PyModbus can be installed easily like this:

```
pip3 install pyyaml
pip3 install PyModbus
```

Now download the files of *this* repository to any location of your choise.
Then copy `config.yaml` from the `templates` directory to the project root (=same directory where `MTECmodbusAPI.py` is located).

In order to connect to your individual device, you need the IP Address of your `espressif` device. 
1. Login to your Internet router
2. Look for the list of connected devices
3. You should find a devices called `espressif`
4. Copy the IPv4 address of this device to `config.yaml` file as value for `MODBUS_IP``

```
# MODBUS Server
MODBUS_IP : "xx.xx.xx.xx"   # IP address of "espressif" modbus server
MODBUS_PORT : 5743          # Port (usually no change required)
MODBUS_SLAVE : 252          # Modbus slave id (usually no change required)
```

That's all you need to do!

## Commandline tool
Having done the setup, you already should be able to start the command line tool `MTEC_tool.py`.
As default, it will connect to your device and retrieve a list of all known parameters in human readable format.

By specifying commandline parameters, you can:
* Toggle between a full export of all parameters `-t full` or a subset of the essential ones `-t essential`
* Provide a customize list of addresses (=parameter id's) which you would like to retrieve, e.g. `-a 33000,10105,11000`
* Request to export CSV instead of human readable (`-c`) 
* Write output to a file (`-f FILENAME`)

## MQTT server
The MQTT server `MTEC_modbus_mqtt.py` enables to export inverter data to a MQTT broker. This can be useful, if you want to use the data e.g. as source for an EMS or home automation tool. Many of them enable to read data from MQTT, therefore this might be a good option for an easy integration.

### Configuration
Please see following options in `config.yaml` to configurate the service according your demand:

```
MQTT_SERVER : "localhost"   # MQTT server 
MQTT_PORT : 1883            # MQTT server port
MQTT_LOGIN  : " "           # MQTT Login
MQTT_PASSWORD : ""          # MQTT Password  
MQTT_TOPIC : "MTEC"         # MQTT topic name  

POLL_FREQUENCY : 10         # query data every N seconds
DEBUG : True                # Set to True to get verbose debug messages

MQTT_FLOAT_FORMAT : "{:.2f}"    # Defines how to format float values
```

### Data format written to MQTT
The script will login to your espressif Modbus server and will write the relevant data to MQTT every `POLL_FREQUENCY` seconds. 

The data will be written to a MQTT topic, using the naming: `MTEC/<parameter>`

| Parameter             | Type  | Unit | Description 
|---------------------- | ----- | ---- | ---------------------------------------------- 
| day_production        | float | kWh  | Energy produced by the PV today 
| total_production      | float | kWh  | Energy produced by the PV in total
| current_PV            | float | W    | Current flow from PV 
| current_grid          | float | W    | Current flow to/from grid (flow to grid is represented by pos. values)
| current_battery       | float | W    | Current flow to/from battery (flow from battery is represented by pos. values)
| current_inverter      | float | W    | Current flow to/from inverter (flow from inverter is represented by pos. values)
| current_house         | float | W    | Current house consumption 
| current_battery_SOC   | int   | %    | Current battery SOC
| inverter_status       | int   |      | 0:wait for on-grid, 1:self-check, 2:on grid, 3:fault, 4:firmware update, 5:off grid 

All `float` values will be written according to the configured `MQTT_FLOAT_FORMAT`. The default is a format with 2 decimal digits.

This diagram should help to understand the power flow values:
<pre>
     + ->               + ->                    + -> 
PV  -------  inverter  ------- power connector ------- grid                
                |                     |
                | ^                 + |
                | +                 v |
Battery ---------                     --------- house
</pre>

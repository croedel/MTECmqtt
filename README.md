# M-TEC Modbus API
Welcome to the `M-TEC Modbus API` project!

This is actually my second approach to read data from a M-TEC Energybutler (https://www.mtec-systems.com) system.
My first approach was to use the Web-portal - you can find the outcome at my project `M-TEC API`.

After more research, I am happy to proudly present my second approach!

The highlights are:
* No additional hardware or modifications of your Inverter required
* Uses the standard communication protocol 'Modbus RTU over TCP' 
* Enables to read out more than 70 parameters from your Inverter
* Works within you LAN - no internet connection required
* Enables fast polling of essential data (e.g. every 10s)
* Easy to use commandline-tool and MQTT broker integration, enabling an easy integration into almost any EMS or home automation tool

I hope you like it and it will help you with for your EMS or home automation project :-) !

## Disclaimer 
In order not to do uninteneded changes or settings and avoid any side-effects, I intentionally implemented read functionality only. 

_Disclaimer:_ This project is a pure hobby project which I created by reverse-engineering different internet sources and my M-TEC Energybutler. It is *not* related to or supported by M-TEC GmbH by any means. Usage is on you own risk. I don't take any responsibility on functionality or potential damage.

## Credits
This project would not have been possible without the really valuable pre-work of other people, especially: 
* https://www.photovoltaikforum.com/thread/206243-erfahrungen-mit-m-tec-energy-butler-hybrid-wechselrichter
* https://forum.iobroker.net/assets/uploads/files/1681811699113-20221125_mtec-energybutler_modbus_rtu_protkoll.pdf
* https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol

## Compatibility
The project was developed using my `M-TEC Energybutler 8kW-3P-3G25`, but I assume that it will also work with other Energybutler GEN3 versions (https://www.mtec-systems.com/batteriespeicher/energy-butler-11-bis-30-kwh/).

It seems that there are at least three more Inverter products on the market which share the same (or at least a very similar) Chinese firmware. It *might* be that this API also works with these products. But since I do not have access to any of them, this is just a guess and up to you and your own risk to try it.

| Provider  | Link 
|---------- | -------------------------------------- 
| Wattsonic | https://www.wattsonic.com/ |
| Sunways   | https://de.sunways-tech.com |
| Daxtromn  | https://daxtromn-power.com/products/ |


## What the MTEC Modbus API offers
### API
The actual API can be found in `MTECmodbusAPI.py`. It offers functionality to:
* Connect to the Modbus RTU server of your inverter 
* Retrieve current status and usage data

The main function of the API is `read_modbus_data(ip_addr, port, slave, addresses=None)`.
It either fetches all known addresses (addresses=None) or you can specify a list of addresses (e.g. addresses=['10105', '11000']) and returns a map, containing the nicely formatted data.

The map should be self-explaining and looks like this:
```
{ 
  '10105': {'name': 'Inverter Running Status', 'value': 2, 'unit': ''}, 
  '11000': {'name': 'Total Power on Meter', 'value': 0.036, 'unit': 'kW'}, 
  '11016': {'name': 'P_AC', 'value': 0.79, 'unit': 'kW'}, 
}
```

### Commandline tool
The command-line tool `MTEC_tool.py` offers functionality to export the data in various combinations and formats.
It also shows how to use the API, if you e.g. want to integrate it into your own project.

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
| api_date              | str   |      | Local date from API server YY/MM/DD HH:MM:SS 
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

This diagram should help to understand the power flow values and directions:
<pre>
     + ->               + ->                    + -> 
PV  -------  inverter  ------- power connector ------- grid                
                |                     |
                | ^                 + |
                | +                 v |
Battery ---------                     --------- house
</pre>

## Supported addresses

The API currently supports following addresses:

| Address |  Description 
|------- | ---------------------------------------------- 
| 10000  | Inverter serial number |  
| 10008  | Equipment Info	    |
| 10011  | Firmware Version       |
| 10100  | Inverter date          |                   	
| 10105  | Inverter Running Status |      
| 10112  | Fault Flag1         | 
| 10114  | Fault Flag2         | 
| 10120  | Fault Flag3         | 
| 10994  | Phase A Power on Meter |	                
| 10996  | Phase B Power on Meter |	                
| 10998  | Phase C Power on Meter |	                
| 11000  | Total Power on Meter |	                     
| 11002  | Total Grid-Injection Energy on Meter |	      
| 11004  | Total Purchasing Energy from Grid on Meter |
| 11006  | Grid Lines A/B Voltage |	                
| 11007  | Grid Lines B/C Voltage |	                
| 11008  | Grid Lines C/A Voltage |	                
| 11009  | Grid Phase A Voltage |	                     
| 11010  | Grid Phase A Current |	                     
| 11011  | Grid Phase B Voltage |	                     
| 11012  | Grid Phase B Current |	                     
| 11013  | Grid Phase C Voltage |	                     
| 11014  | Grid Phase C Current |	                     
| 11015  | Grid Frequency |	                          
| 11016  | P_AC |	                                    
| 11018  | Total PV Generation on that day |	          
| 11020  | Total PV Generation from Installation |      
| 11022  | Total PV Generation Time from Installation |
| 11028  | PV Input Total Power |	                     
| 11032  | Temperature Sensor 1 |	                     
| 11033  | Temperature Sensor 2 |	                     
| 11034  | Temperature Sensor 3 |	                     
| 11035  | Temperature Sensor 4 |	                     
| 11038  | PV1 Voltage |	                              
| 11039  | PV1 Current |	                              
| 11040  | PV2 Voltage |	                              
| 11041  | PV2 Current |	                              
| 11062  | PV1 Input Power |                            
| 11064  | PV2 Input Power |                            
| 30200  | Backup_A_V |	                               
| 30201  | Backup_A_I |	                               
| 30202  | Backup_A_F |	                               
| 30204  | Backup_A_P |	                               
| 30210  | Backup_B_V |	                               
| 30211  | Backup_B_I |	                               
| 30212  | Backup_B_F |	                               
| 30214  | Backup_B_P |	                               
| 30220  | Backup_C_V |	                               
| 30221  | Backup_C_I |	                               
| 30222  | Backup_C_F |	                               
| 30224  | Backup_C_P |	                               
| 30230  | Total_Backup_P |	                          
| 30236  | Invt_A_P |	                               
| 30242  | Invt_B_P |	                               
| 30248  | Invt_C_P |	                               
| 30254  | Battery_V |	                               
| 30255  | Battery_I |	                               
| 30256  | Battery_Mode |	                          
| 30258  | Battery_P |                                  
| 31000  | Grid Injection Energy on that day[Meter] |	 
| 31001  | Grid Purchasing Energy on that day[Meter] |  
| 31002  | Backup Output Energy on that day |	      
| 31003  | Battery Charge Energy on that day |          
| 31004  | Battery Discharge Energy on that day |	      
| 31005  | PV Generation Energy on that day |	      
| 31006  | Loading Energy on that day |	                
| 31008  | Energy Purchased from Grid on that day |	 
| 31102  | Total Energy injected to grid |              
| 31104  | Total Energy Purchased from Grid from Meter |
| 31106  | Total Output Energy on backup port |	      
| 31108  | Total Energy Charged to Battery |            
| 31110  | Total Energy Discharged from Battery |	      
| 31112  | Total PV Generation |                        
| 31114  | Total Loading Energy consumed at grid side |
| 31118  | Total Energy Purchased from Grid |           
| 33000  | SOC |	                                    
| 33001  | SOH |	                                    
| 33002  | BMS Status |	                               
| 33003  | BMS Pack Temperature |	                     
| 33009  | Max Cell Temperature |	                     
| 33011  | Min Cell Temperature |	                     
| 33013  | Max Cell Voltage |	                          
| 33015  | Min Cell Voltage |	                          

Many thanks to https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol/ for the fabulous collection of the addresses!

# M-TEC MQTT

## Introduction
Welcome to the `M-TEC MQTT` project!

This project provides a service which reads data from a M-TEC Energybutler (https://www.mtec-systems.com) system and writes them to a MQTT broker. 

The highlights are:
* Just install on any existing (micro-)server, e.g. Rasperry Pi or NAS server 
* No additional hardware or modifications of your Inverter required 
* MQTT enables an easy integration into almost any EMS or home automation tool 
* Home Assistant (https://www.home-assistant.io) auto discovery via MQTT 
* Easy and prepared integration into evcc (https://evcc.io), which enables PV surplus charging 
* Works within you LAN - no internet connection required
* Uses the standard communication protocol 'Modbus RTU over TCP' to read the data from the Inverter 
* Enables frequent polling of essential data (e.g. every 10s)
* Enables to read out more than 80 parameters from your Inverter

I hope you like it and it will help you with for your EMS or home automation project :-) !

### Disclaimer 
In order not to do uninteneded changes or settings and avoid any side-effects, I intentionally implemented read functionality only. 

_Disclaimer:_ This project is a pure hobby project which I created by reverse-engineering different internet sources and my M-TEC Energybutler. It is *not* related to or supported by M-TEC GmbH by any means. Usage is on you own risk. I don't take any responsibility on functionality or potential damage.

### Credits
This project would not have been possible without the really valuable pre-work of other people, especially: 
* https://www.photovoltaikforum.com/thread/206243-erfahrungen-mit-m-tec-energy-butler-hybrid-wechselrichter
* https://forum.iobroker.net/assets/uploads/files/1681811699113-20221125_mtec-energybutler_modbus_rtu_protkoll.pdf
* https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol

### Compatibility
The project was developed using my `M-TEC Energybutler 8kW-3P-3G25`, but I assume that it will also work with other Energybutler GEN3 versions (https://www.mtec-systems.com/batteriespeicher/energy-butler-11-bis-30-kwh/).

It seems that there are at least three more Inverter products on the market which share the same (or at least a very similar) Chinese firmware. It *might* be that this API also works with these products. But since I do not have access to any of them, this is just a guess and up to you and your own risk to try it.

| Provider  | Link 
|---------- | -------------------------------------- 
| Wattsonic | https://www.wattsonic.com/ |
| Sunways   | https://de.sunways-tech.com |
| Daxtromn  | https://daxtromn-power.com/products/ |


## MQTT server
The MQTT server `mtec_mqtt.py` connects to the espressif Modbus server of you M-TEC inverter, retrieves relevant data, and writes them to a MQTT broker (https://mqtt.org/) of your choice. 

You should be able to use it with probably any MQTT server. If you don't have one yet, you might want to try https://mosquitto.org/.

MQTT provides a light-weight publish/subscribe model which is widely used for Internet of Things messaging. MQTT connectivity is implemented in many EMS or home automation tools. 

`mtec_mqtt.py` provides Home Assistant (https://www.home-assistant.io) auto-discovery, which means that Home Assistant will automatically detect and configure your MTEC Inverter. You just need to enable and configure the MQTT integration within Home Assistant and then start `mtec_mqtt.py`.  

If you want to integrate the data into evcc (https://evcc.io), you might want to have a look at the `èvcc.yaml` snippet in the `templates` directory. It shows how to define and use the MTEC `meters`, provided in MQTT.
Please don't forget to replace `<MTEC_SERIAL_NO>` with the actual serial no of your Inverter.

If you want to run the mqtt server as a service, you can find a `.service` template in the `templates` directory. 

## Setup & configuration
As prerequisites, you need to have installed: 
* Python 3.8 or higher
* PyYAML 
* PyModbus
* paho-mqtt 

I recommend to install it in a `venv`.
The python modules can be installed easily by using `pip`:

```
pip install pyyaml
pip install PyModbus
pip install paho-mqtt
```

Now download the files of *this* repository to any location of your choise.
Then copy `config.yaml` from the `templates` directory to the project root.

Now you need to configure:
* Connect your M-TEC Inverter
* Connect you MQTT broker
 
### Connect your M-TEC Inverter
In order to connect to your Inverter, you need the IP Address of your `espressif` device. 
1. Login to your internet router
2. Look for the list of connected devices
3. You should find a devices called `espressif`
4. Copy the IPv4 address of this device to `config.yaml` file as value for `MODBUS_IP`

```
# MODBUS Server
MODBUS_IP : "xx.xx.xx.xx"   # IP address of "espressif" modbus server
MODBUS_PORT : 5743          # Port (usually no change required)
MODBUS_SLAVE : 252          # Modbus slave id (usually no change required)
MODBUS_TIMEOUT : 5          # Timeout for Modbus server (s)
```

### Connect you MQTT broker
The `MQTT_` parameters in `config.yaml` define the connection to your MQTT server.

```
MQTT_SERVER : "localhost"   # MQTT server 
MQTT_PORT : 1883            # MQTT server port
MQTT_LOGIN  : " "           # MQTT Login
MQTT_PASSWORD : ""          # MQTT Password  
MQTT_TOPIC : "MTEC"         # MQTT topic name  
```

The other values of the `config.yaml` you probably don't need to change as of now.
That's all you need to do!

### Advanced config
The `REFRESH_` parameters define how frequently the data gets fetched from your Inverter

```
REFRESH_CURRENT_S : 10          # Refresh "current" data every N seconds
REFRESH_DAY_M     : 5           # Refresh "day" statistic every N minutes
REFRESH_TOTAL_M   : 5           # Refresh "total" statistic every N minutes
REFRESH_CONFIG_H  : 24          # Refresh "config" data every N hours

MQTT_FLOAT_FORMAT : "{:.2f}"    # Defines how to format float values
```

If require, you can disable Home Automation auto discovery and/or configure a different MQTT base topic: 

```
# Home Assistent
HASS_ENABLE : True                  # Enable home assistant
HASS_BASE_TOPIC : "homeassistant"   # Basis MQTT topic of home assistant
```

## Data format written to MQTT

The data will be written to 4 MQTT topics. The topic path includes the serial number of your Inverter.
 
| Sub-topic                         | Refresh frequency            |  Description 
|---------------------------------- | --------------------------   | ---------------------------------------------- 
| MTEC/<serial_number>/config       | `REFRESH_CONFIG_H` hours     | Relatively static config values     
| MTEC/<serial_number>/current      | `REFRESH_CURRENT_S` seconds  | Current data      
| MTEC/<serial_number>/day          | `REFRESH_DAY_M` minutes      | Daily statistics     
| MTEC/<serial_number>/total        | `REFRESH_TOTAL_M` minutes    | Lifetime statistics     

All `float` values will be written according to the configured `MQTT_FLOAT_FORMAT`. The default is a format with 3 decimal digits.

This diagram tries to visualize the power flow values and directions: (at least from my understanding)
<pre>
     + ->               + ->                    + -> 
PV  -------  inverter  ------- power connector ------- grid                
              |    |                |
            ^ |    | +            + |
            + |    | v            v |
Battery -------    |                --------- house
                   -------------------------- backup power
</pre>

*Remark:* The parameters marked by `(*)` are calculated values. 

### config
| Parameter               | Type  | Unit | Description 
|----------------------   | ----- | ---- | ---------------------------------------------- 
| api_date                | str   |      | Local date from API server YYYY-MM-DD HH:MM:SS 
| serial_no               | str   |      | Inverter serial number 
| firmware_version        | str   |      | Inverter firmware version 

### current
| Parameter               | Type  | Unit | Description 
|----------------------   | ----- | ---- | ---------------------------------------------- 
| api_date                | str   |      | Local date from API server YYYY-MM-DD HH:MM:SS 
| inverter_date           | str   |      | Date from inverter YY-MM-DD HH:MM:SS 
| inverter_status         | int   |      | 0:wait for on-grid, 1:self-check, 2:on grid, 3:fault, 4:firmware update, 5:off grid 
| PV                      | float | W    | Current power generated by PV 
| grid                    | float | W    | Current power flow to/from grid (flow to grid is represented by pos. values)
| battery                 | float | W    | Current power flow to/from battery (flow from battery is represented by pos. values)
| inverter                | float | W    | Current power flow to/from inverter (flow from inverter is represented by pos. values)
| backup                  | float | W    | Current backup power flow
| consumption             | float | W    | Current consumption 
| battery_SOC             | int   | %    | Current battery SOC

### day
| Parameter               | Type  | Unit | Description 
|----------------------   | ----- | ---- | ---------------------------------------------- 
| api_date                | str   |      | Local date from API server YYYY/MM/DD HH:MM:SS 
| PV                      | float | kWh  | Energy generated PV today 
| grid_feed               | float | kWh  | Energy feed into grid today
| grid_purchase           | float | kWh  | Energy purchased from grid today
| battery_charge          | float | kWh  | Energy charged to battery today
| battery_discharge       | float | kWh  | Energy discharged from battery today
| consumption             | float | kWh  | Own energy consumption today (*)
| autarky_rate            | float | %    | Autarky rate today (*)
| own_consumption_rate    | float | %    | Own consumption rate today (*)

### total
| Parameter               | Type  | Unit | Description 
|----------------------   | ----- | ---- | ---------------------------------------------- 
| api_date                | str   |      | Local date from API server YYYY/MM/DD HH:MM:SS 
| PV                      | float | kWh  | Energy generated PV 
| grid_feed               | float | kWh  | Energy feed into grid 
| grid_purchase           | float | kWh  | Energy purchased from grid 
| battery_charge          | float | kWh  | Energy charged to battery 
| battery_discharge       | float | kWh  | Energy discharged from battery 
| consumption             | float | kWh  | Own energy consumption (*)
| autarky_rate            | float | %    | Autarky rate (*)
| own_consumption_rate    | float | %    | Own consumption rate (*)


## What else you can find in the project?

### Commandline tool
The command-line tool `mtec_tool.py` offers functionality to export the data in various combinations and formats.

As default, it will connect to your device and retrieve a list of all known Modbus registers in a human readable format.

By specifying commandline parameters, you can:
* Toggle between a full export of all registers `-t all` or a subset of the essential ones `-t essential`
* Provide a customize list of Modbus registers which you would like to retrieve, e.g. `-r 33000,10105,11000`
* Request to export CSV instead of human readable (`-c`) 
* Write output to a file (`-f FILENAME`)

### Supported registers
The API currently supports the Modbus registers listed below. 

Many thanks to https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol/ for the fabulous collection of the registers!

I can't say what each of these registers exactly means. Some data seams quite reliable and comprehensible - others is probably questionable.

| Register |  Description 
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

# M-TEC MQTT

## Introduction
Welcome to the `M-TEC MQTT` project!

This project enables to read data from a M-TEC Energybutler (https://www.mtec-systems.com) system and write them to a MQTT broker. 

The highlights are:
* No additional hardware or modifications of your Inverter required 
* Just install on any existing (micro-)server, e.g. Rasperry Pi or NAS server 
* Works within you LAN - no internet connection required 
* Supports more than 80 parameters
* Clustered reading of sequential register to reduce modbus traffic and load 
* Enables frequent polling of data (e.g. every 10s)
* MQTT enables an easy integration into almost any EMS or home automation tool 
* Home Assistant (https://www.home-assistant.io) auto discovery via MQTT 
* Home Assistant demo dashboard included
* Easy and prepared integration into evcc (https://evcc.io), which enables PV surplus charging 

I hope you like it and it will help you with for your EMS or home automation project :-) !

### Disclaimer 
This project is a pure hobby project which I created by reverse-engineering different internet sources and my M-TEC Energybutler. It is *not* related to or supported by M-TEC GmbH by any means. 

Usage is completely on you own risk. I don't take any responsibility on functionality or potential damage.

### Credits
This project would not have been possible without the really valuable pre-work of other people, especially: 
* https://www.photovoltaikforum.com/thread/206243-erfahrungen-mit-m-tec-energy-butler-hybrid-wechselrichter
* https://forum.iobroker.net/assets/uploads/files/1681811699113-20221125_mtec-energybutler_modbus_rtu_protkoll.pdf
* https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol
* The Home Assistant "blue theme" background was thankfully provided by Enrico from redK! Webdesign & Content Management

### Compatibility
The project was developed using my `M-TEC Energybutler 8kW-3P-3G25`, but I assume that it will also work with other Energybutler GEN3 versions (https://www.mtec-systems.com/batteriespeicher/energy-butler-11-bis-30-kwh/).

It seems that there are at least three more Inverter products on the market which share the same (or at least a very similar) Chinese firmware. It *might* be that this API also works with these products. But since I do not have access to any of them, this is just a guess and up to you and your own risk to try it.

| Provider  | Link 
|---------- | -------------------------------------- 
| Wattsonic | https://www.wattsonic.com/ |
| Sunways   | https://de.sunways-tech.com |
| Daxtromn  | https://daxtromn-power.com/products/ |


## MQTT server
The MQTT server `mtec_mqtt` connects to the espressif Modbus server of you M-TEC inverter, retrieves relevant data, and writes them to a MQTT broker (https://mqtt.org/) of your choice. 
MQTT provides a light-weight publish/subscribe model which is widely used for Internet of Things messaging. MQTT connectivity is implemented in many EMS or home automation tools. 

## Setup & configuration
### Prerequesits
Please make sure you have installed Python 3.8 or higher.

As said before, the projects communicated using MQTT. That means, you require a MQTT server. If you don't have one yet, you might want to try https://mosquitto.org/. 
You can easily install it like this:

```
sudo apt install mosquitto mosquitto-clients
```

### Installation
The basic installation requires only following 3 steps:

(1) Create a new directory for the installation (e.g. within your HOME directory) and create and activate a virtual python environment for the project.
```
mkdir mtecmqtt && cd mtecmqtt && python3 -m venv . && source bin/activate
```

(2) Download the MTECmqtt project from github
```
wget https://github.com/croedel/MTECmqtt/archive/refs/heads/main.zip && unzip main.zip && rm main.zip
```

(3) Execute the project setup.py 
```
cd MTECmqtt-main && python3 setup.py install && cd ..
```

This is all you need to do for a standard setup! 

As a next step, we can try to start the MQTT server. It will print out some debug info, so you can see what it does.
```
mtec_mqtt.py
```
You can stop the service by pressing CTRL-C or sending a SIGHUB. This will initiate a graceful shutdown. Please be patient - this might take a few seconds.

Starting the service in a shell - as we just did - will not create a permanent running service and is probably only useful for testing. If you want a permanently running service, you need to install a systemd autostart script for `mtec_mytt.py`. The following command does this job:
```
sudo bin/install_systemd_service.sh 
```

To check if the service is running smoothly, you can execute:
```
sudo systemctl status mtec_mqtt
```

### Advanced configuration 
This section give you more information about all configuration options. But don't be afraid - it should only be relevant for advanced use cases.

#### Connect your M-TEC Inverter
In order to connect to your Inverter, you need the IP address or internal hostname of your `espressif` device. 
If you run a FRITZ!Box, the pre-configured internal hostname `espressif.fritz.box` will probably already work out-of-the-box.
Else you can easily adjust it like this: 
1. Login to your internet router
2. Look for the list of connected devices
3. You should find a devices called `espressif`
4. Copy the IPv4 address or internal hostname of this device to `config.yaml` file as value for `MODBUS_IP`.

You probably don't need to change any of the other `MODBUS_` config values.

```
# MODBUS Server
MODBUS_IP : espressif.fritz.box    # IP address / hostname of "espressif" modbus server
MODBUS_PORT : 5743                 # Port (usually no change required)
MODBUS_SLAVE : 252                 # Modbus slave id (usually no change required)
MODBUS_TIMEOUT : 5                 # Timeout for Modbus server (s)
MODBUS_FRAMER: rtu                 # Modbus Framer (usually no change required; options: 'ascii', 'binary', 'rtu', 'socket', 'tls')
```

Hint for advanced users: If you run an external modbus adapter, connected e.g. to the EMS bus of the MTEC inverter, you might require to change the `MODBUS_FRAMER`.   

#### Connect you MQTT broker
The `MQTT_` parameters in `config.yaml` define the connection to your MQTT server.

```
MQTT_SERVER : localhost     # MQTT server 
MQTT_PORT : 1883            # MQTT server port
MQTT_LOGIN  : " "           # MQTT Login
MQTT_PASSWORD : ""          # MQTT Password  
MQTT_TOPIC : "MTEC"         # MQTT topic name  
```

The other values of the `config.yaml` you probably don't need to change as of now.

That's already all you need to do and you are ready to go!

#### More configuration options
The `REFRESH_` parameters define how frequently the data gets fetched from your Inverter

```
REFRESH_NOW     : 10          # Refresh current data every N seconds
REFRESH_DAY     : 300         # Refresh daily statistic every N seconds
REFRESH_TOTAL   : 300         # Refresh total statistic every N seconds
REFRESH_CONFIG  : 3600        # Refresh config data every N seconds
``` 

### Home Assistant support
`mtec_mqtt.py` provides Home Assistant (https://www.home-assistant.io) auto-discovery, which means that Home Assistant will automatically detect and configure your MTEC Inverter. 

If you want to enable Home Assistant support, set `HASS_ENABLE: True` in `config.yaml`. 

```
# Home Assistent
HASS_ENABLE : True                # Enable home assistant support
HASS_BASE_TOPIC : homeassistant   # Basis MQTT topic of home assistant
HASS_BIRTH_GRACETIME : 15         # Give HASS some time to get ready after the birth message was received
```

As next step, you need to enable and configure the MQTT integration within Home Assistant. After that, the auto discovery should do it's job and the Inverter sensors should appear on your dashboard.

If you want, you can use and install one of the Home Assistant dashboards in `templates` for a nice data visualization.
The map view requires to install a background image. To do so, create a sub-directory called `www` in the `config` directory of your Home Assistant installation (e.g. `/home/homeassistant/.homeassistant/www/`) and copy the image to this directory.

There are two versions you can chose from:
| Theme       | Dashboard                    | Image
|-------------|--------------------          | ---------------------
| Dark theme  | hass-dashboard.yaml          | PV_background.png
| Blue theme  | hass-dashboard-blue.yaml     | PV_background-blue.png

### evcc support
If you want to integrate the data into evcc (https://evcc.io), you might want to have a look at the `evcc.yaml` snippet in the `templates` directory. It shows how to define and use the MTEC `meters`, provided in MQTT.
Please don't forget to replace `<MTEC_SERIAL_NO>` with the actual serial no of your Inverter.

## Data format written to MQTT

The exported data will be written to several MQTT topics. The topic path includes the serial number of your Inverter.
 
| Sub-topic                         | Refresh frequency            |  Description 
|---------------------------------- | --------------------------   | ---------------------------------------------- 
| MTEC/<serial_number>/config       | `REFRESH_CONFIG` seconds     | Relatively static config values     
| MTEC/<serial_number>/now-base     | `REFRESH_NOW` seconds        | Current base data      
| MTEC/<serial_number>/now-grid     | `REFRESH_NOWEXT` seconds     | Current extended grid data      
| MTEC/<serial_number>/now-inverter | `REFRESH_NOWEXT` seconds     | Current extended inverter data      
| MTEC/<serial_number>/now-backup   | `REFRESH_NOWEXT` seconds     | Current extended backup data      
| MTEC/<serial_number>/now-battery  | `REFRESH_NOWEXT` seconds     | Current extended battery data      
| MTEC/<serial_number>/now-pv       | `REFRESH_NOWEXT` seconds     | Current extended PV data      
| MTEC/<serial_number>/day          | `REFRESH_DAY` seconds        | Daily statistics     
| MTEC/<serial_number>/total        | `REFRESH_TOTAL` seconds      | Lifetime statistics     

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

*Remark:* Some parameters - marked by `(*)` - are calculated values. 

### config
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 10000    | serial_no               |      | Inverter serial number
| 10011    | firmware_version        |      | Firmware version
| 25100    | grid_inject_switch      |      | Grid injection limit switch
| 25103    | grid_inject_limit       | %    | Grid injection power limit
| 52502    | on_grid_soc_switch      |      | On-grid SOC limit switch
| 52503    | on_grid_soc_limit       | %    | On-grid SOC limit
| 52504    | off_grid_soc_switch     |      | Off-grid SOC limit switch
| 52505    | off_grid_soc_limit      | %    | Off-grid SOC limit
|          | api_date                |      | Local date of MTECmqtt server

### now-base
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 10100    | inverter_date           |      | Inverter date
| 10105    | inverter_status         |      | Inverter status (0=wait for on-grid, 1=self-check, 2=on-grid, 3=fault, 4=firmware update, 5=off grid)
| 11000    | grid_power              | W    | Grid power
| 11016    | inverter                | W    | Inverter AC power
| 11028    | pv                      | W    | PV power
| 30230    | backup                  | W    | Backup power total
| 30254    | battery_voltage         | V    | Battery voltage
| 30255    | battery_current         | A    | Battery current
| 30256    | battery_mode            |      | Battery mode (0=Discharge, 1=Charge)
| 30258    | battery                 | W    | Battery power
| 33000    | battery_soc             | %    | Battery SOC
| 50000    | mode                    |      | Inverter operation mode (257=General mode, 258=Economic mode, 259=UPS mode, 512=Off grid 771=Manual mode)
|          | consumption             | W    | Household consumption (*)

### now-backup
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 30200    | backup_voltage_a        | V    | Backup voltage phase A
| 30201    | backup_current_a        | A    | Backup current phase A
| 30202    | backup_frequency_a      | Hz   | Backup frequency phase A
| 30204    | backup_a                | W    | Backup power phase A
| 30210    | backup_voltage_b        | V    | Backup voltage phase B
| 30211    | backup_current_b        | A    | Backup current phase B
| 30212    | backup_frequency_b      | Hz   | Backup frequency phase B
| 30214    | backup_b                | W    | Backup power phase B
| 30220    | backup_voltage_c        | V    | Backup voltage phase C
| 30221    | backup_current_c        | A    | Backup current phase C
| 30222    | backup_frequency_c      | Hz   | Backup frequency phase C
| 30224    | backup_c                | W    | Backup power phase C

### now-battery
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 33001    | battery_soh             | %    | Battery SOH
| 33003    | battery_temp            | ℃   | Battery temperature 
| 33009    | battery_cell_t_max      | ℃   | Battery cell temperature max.
| 33011    | battery_cell_t_min      | ℃   | Battery cell temperature min.
| 33013    | battery_cell_v_max      | V    | Battery cell voltage max.
| 33015    | battery_cell_v_min      | V    | Battery cell voltage min.

### now-grid
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 10994    | grid_a                  | W    | Grid power phase A
| 10996    | grid_b                  | W    | Grid power phase B
| 10998    | grid_c                  | W    | Grid power phase C
| 11006    | ac_voltage_a_b          | V    | Inverter AC voltage lines A/B
| 11007    | ac_voltage_b_c          | V    | Inverter AC voltage lines B/C
| 11008    | ac_voltage_c_a          | V    | Inverter AC voltage lines C/A
| 11009    | ac_voltage_a            | V    | Inverter AC voltage phase A
| 11010    | ac_current_a            | A    | Inverter AC current phase A
| 11011    | ac_voltage_b            | V    | Inverter AC voltage phase B
| 11012    | ac_current_b            | A    | Inverter AC current phase B
| 11013    | ac_voltage_c            | V    | Inverter AC voltage phase C
| 11014    | ac_current_c            | A    | Inverter AC current phase C
| 11015    | ac_fequency             | Hz   | Inverter AC frequency

### now-inverter
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 11032    | inverter_temp1          | ℃  | Temperature Sensor 1
| 11033    | inverter_temp2          | ℃  | Temperature Sensor 2
| 11034    | inverter_temp3          | ℃  | Temperature Sensor 3
| 11035    | inverter_temp4          | ℃  | Temperature Sensor 4
| 30236    | inverter_a              | W   | Inverter power phase A
| 30242    | inverter_b              | W   | Inverter power phase B
| 30248    | inverter_c              | W   | Inverter power phase C

### now-pv
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 11022    | pv_generation_duration  | h    | PV generation time total
| 11038    | pv_voltage_1            | V    | PV1 voltage
| 11039    | pv_current_1            | A    | PV1 current
| 11040    | pv_voltage_2            | V    | PV2 voltage
| 11041    | pv_current_2            | A    | PV2 current
| 11062    | pv_1                    | W    | PV1 power
| 11064    | pv_2                    | W    | PV2 power

### day
| Register | MQTT Parameter          | Unit | Description 
| -------- | ----------------------  | ---- | ---------------------------------------------- 
| 31000    | grid_feed_day           | kWh  | Grid injection energy (day)
| 31001    | grid_purchase_day       | kWh  | Grid purchased energy (day)
| 31002    | backup_day              | kWh  | Backup energy (day)
| 31003    | battery_charge_day      | kWh  | Battery charge energy (day)
| 31004    | battery_discharge_day   | kWh  | Battery discharge energy (day)
| 31005    | pv_day                  | kWh  | PV energy generated (day)
|          | autarky_rate_day        | %    | Household autarky (day) (*)
|          | consumption_day         | kWh  | Household energy consumed (day) (*)
|          | own_consumption_day     | %    | Own consumption rate (day) (*)

### total
| Register | MQTT Parameter             | Unit | Description 
| -------- | ----------------------     | ---- | ---------------------------------------------- 
| 31102    | grid_feed_total            | kWh  | Grid energy injected (total)
| 31104    | grid_purchase_total        | kWh  | Grid energy purchased (total)
| 31106    | backup_total               | kWh  | Backup energy (total)
| 31108    | battery_charge_total       | kWh  | Battery energy charged (total)
| 31110    | battery_discharge_total    | kWh  | Battery energy discharged (total)
| 31112    | pv_total                   | kWh  | PV energy generated (total)
|          | autarky_rate_total         | %    | Household autarky (total) (*)
|          | consumption_total          | kWh  | Household energy consumed (total) (*)
|          | own_consumption_total      | %    | Own consumption rate (total) (*)


## What else you can find in the project?

### Modbus Utility
`mtec_util.py` is an small inteative tool which enable to list the supported parameters and read and write registers of your Inverter.
You can choose between:

 * 1: List all known registers
 * 2: List register configuration by groups
 * 3: Read register group from Inverter
 * 4: Read single register from Inverter
 * 5: Write register to Inverter

(1) lists all know registers. This includes the ones which are written to MQTT as listed above. You will find a few more registers, which are not mapped to MQTT (=no value in "mqtt") - mostly because I'm not sure if they are reliable or what they really mean.   

(2) will give you a list of all mapped registers, similar to the one listed above.

(3) allows you to read the current values of all registers or of a certain group from your Inverter.

(4) allows you to read a sinfle register from your Inverter

(5) enables you to write a value to a register of your Inverter. WARNING: Be careful when writing data to your Inverter! This is definitively at your own risk!

### Commandline export tool
The command-line tool `mtec_export.py` offers functionality to read data from your Inverter using Modbus and export it in various combinations and formats.

As default, it will connect to your device and retrieve a list of all known Modbus registers in a human readable format.

By specifying commandline parameters, you can:
* Specify a register group (e.g. `-g config`) or "all" (`-g all`) to export of all registers
* Provide a customize list of Modbus registers which you would like to retrieve, e.g. `-r "33000,10105,11000"`
* Request to export CSV instead of human readable (`-c`) 
* Write output to a file (`-f FILENAME`)

### Templates 
In the `templates` directory you can find some more useful templates:
* `evcc.yaml`: A yaml snippet shich shows how to integrate your Inverter into evcc.
* `mtec_mqtt.service`: A template which shows how to create a systemctl service running `mtec_mqtt.py`  
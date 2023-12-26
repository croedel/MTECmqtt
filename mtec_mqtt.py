#!/usr/bin/env python3
"""
MQTT server for M-TEC Energybutler reading modbus data
(c) 2023 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from config import cfg
from datetime import datetime, timedelta
import time
import signal
import mqtt
import MTECmodbusAPI
import hass_int

#----------------------------------
def signal_handler(signal_number, frame):
  global run_status
  logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
  run_status = False

#----------------------------------
# map MQTT parameters and modbus registers
param_map = [
  # parameter             # register  # group
  [ "serial_no",          "10000",    "config" ],    
  [ "firmware_version",   "10011",    "config" ],    

  [ "inverter_date",      "10100",    "now-base" ],    
  [ "inverter_status",    "10105",    "now-base" ],    
  [ "pv",                 "11028",    "now-base" ],    
  [ "grid",               "11000",    "now-base" ],    
  [ "battery",            "30258",    "now-base" ],    
  [ "inverter",           "11016",    "now-base" ],    
  [ "backup",             "30230",    "now-base" ],    
  [ "battery_soc",        "33000",    "now-base" ],    
  [ "mode",               "50000",    "now-base" ],    

  [ "grid_frequency",     "11015",    "now-grid" ],    
  [ "grid_a",             "10994",    "now-grid" ],    
  [ "grid_b",             "10996",    "now-grid" ],    
  [ "grid_c",             "10998",    "now-grid" ],    

  [ "grid_inject_switch", "25100",    "now-inverter" ],
  [ "grid_inject_limit",  "25103",    "now-inverter" ],
  [ "on_grid_soc_switch", "52502",    "now-inverter" ],
  [ "on_grid_soc_limit",  "52503",    "now-inverter" ],
  [ "off_grid_soc_switch", "52504",   "now-inverter" ],
  [ "off_grid_soc_limit", "52505",    "now-inverter" ],
  [ "inverter_voltage_a", "11009",    "now-inverter" ],
  [ "inverter_current_a", "11010",    "now-inverter" ],
  [ "inverter_a",         "30236",    "now-inverter" ],
  [ "inverter_voltage_b", "11011",    "now-inverter" ],
  [ "inverter_current_b", "11012",    "now-inverter" ],
  [ "inverter_b",         "30242",    "now-inverter" ],
  [ "inverter_voltage_c", "11013",    "now-inverter" ],
  [ "inverter_current_c", "11014",    "now-inverter" ],
  [ "inverter_c",         "30248",    "now-inverter" ],
  [ "inverter_temp1",     "11032",    "now-inverter" ],
  [ "inverter_temp2",     "11033",    "now-inverter" ],
  [ "inverter_temp3",     "11034",    "now-inverter" ],
  [ "inverter_temp4",     "11035",    "now-inverter" ],

  [ "backup_voltage_a",   "30200",    "now-backup" ],  
  [ "backup_current_a",   "30201",    "now-backup" ],  
  [ "backup_frequency_a", "30202",    "now-backup" ],  
  [ "backup_a",           "30204",    "now-backup" ],  
  [ "backup_voltage_b",   "30210",    "now-backup" ],  
  [ "backup_current_b",   "30211",    "now-backup" ],  
  [ "backup_frequency_b", "30212",    "now-backup" ],  
  [ "backup_b",           "30214",    "now-backup" ],  
  [ "backup_voltage_c",   "30220",    "now-backup" ],  
  [ "backup_current_c",   "30221",    "now-backup" ],  
  [ "backup_frequency_c", "30222",    "now-backup" ],  
  [ "backup_c",           "30224",    "now-backup" ],  

  [ "battery_soh",        "33001",    "now-battery" ], 
  [ "battery_voltage",    "30254",    "now-battery" ], 
  [ "battery_current",    "30255",    "now-battery" ], 
  [ "battery_mode",       "30256",    "now-battery" ], 
  [ "battery_cell_t_max", "33009",    "now-battery" ], 
  [ "battery_cell_t_min", "33011",    "now-battery" ], 
  [ "battery_cell_v_max", "33013",    "now-battery" ], 
  [ "battery_cell_v_min", "33015",    "now-battery" ], 

  [ "pv_voltage_1",       "11038",    "now-pv" ],         
  [ "pv_current_1",       "11039",    "now-pv" ],         
  [ "pv_1",               "11062",    "now-pv" ],         
  [ "pv_voltage_2",       "11040",    "now-pv" ],         
  [ "pv_current_2",       "11041",    "now-pv" ],         
  [ "pv_2",               "11064",    "now-pv" ],         

  [ "PV",                 "31005",    "day" ],            
  [ "grid_feed",          "31000",    "day" ],            
  [ "grid_purchase",      "31001",    "day" ],         
  [ "battery_charge",     "31003",    "day" ],        
  [ "battery_discharge",  "31004",    "day" ],       

  [ "PV",                 "31112",    "total" ],          
  [ "grid_feed",          "31102",    "total" ],          
  [ "grid_purchase",      "31104",    "total" ],          
  [ "battery_charge",     "31108",    "total" ],          
  [ "battery_discharge",  "31110",    "total" ],   
]

# =============================================
# MTEC Modbus read
# Helper to get list of registers to read
def get_register_list( category ):
  items = []
  registers = []
  for item in param_map:
    if item[2] == category:
      items.append(item)
      registers.append(item[1])

  if len(registers)==0:
    logging.error("Unknown read category: {}".format(category))
    return None              
  return items, registers

#----------------------------------
# read data from MTEC modbus
def read_MTEC_data( api, category ):
  logging.info("Reading registers for category: {}".format(category))
  items, registers = get_register_list( category )
  now = datetime.now()
  data = api.read_modbus_data(registers=registers)
  pvdata = {}
  try:
    pvdata["api_date"] = now.strftime("%Y-%m-%d %H:%M:%S") # Local time of this server
    # assign all data
    for item in items:
      pvdata[item[0]] = data[item[1]]

    # calculate some additional data
    if category == "now-base":  
      pvdata["consumption"] = data["11016"]["value"] - data["11000"]["value"]  # power consumption 
    elif category == "day":  
      pvdata["consumption"] = data["31005"]["value"] + data["31001"]["value"] + data["31004"]["value"] - data["31000"]["value"] - data["31003"]["value"]  # power consumption 
      pvdata["autarky_rate"] = 100*(1 - (data["31001"]["value"] / pvdata["consumption"])) if pvdata["consumption"]>0 else 0 
      pvdata["own_consumption_rate"] = 100*(1-data["31000"]["value"] / data["31005"]["value"]) if data["31005"]["value"]>0 else 0
    elif category == "total":  
      pvdata["consumption"] = data["31112"]["value"] + data["31104"]["value"] + data["31110"]["value"] - data["31102"]["value"] - data["31108"]["value"]  # power consumption 
      pvdata["autarky_rate"] = 100*(1 - (data["31104"]["value"] / pvdata["consumption"])) if pvdata["consumption"]>0 else 0
      pvdata["own_consumption_rate"] = 100*(1-data["31102"]["value"] / data["31112"]["value"]) if data["31112"]["value"]>0 else 0
 
  except Exception as e:
    logging.warning("Retrieved Modbus data is incomplete: {}".format(str(e)))
    return None
  return pvdata

#----------------------------------
# write data to MQTT
def write_to_MQTT( pvdata, base_topic ):
  for param, data in pvdata.items():
    topic = base_topic + param
    if isinstance(data, dict):
      if isinstance(data["value"], float):  
        payload = cfg['MQTT_FLOAT_FORMAT'].format( data["value"] )
      elif isinstance(data["value"], bool):  
        payload = "{:d}".format( data["value"] )
      else:
        payload = data["value"]
    else:   
      if isinstance(data, float):  
        payload = cfg['MQTT_FLOAT_FORMAT'].format( data )
      elif isinstance(data, bool):  
        payload = "{:d}".format( data )
      else:
        payload = data  
    mqtt.mqtt_publish( topic, payload )

#==========================================
def main():
  global run_status
  run_status = True 

  # Initialization
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)
  logging.info("Starting")

  next_read_config = datetime.now()
  next_read_day = datetime.now()
  next_read_total = datetime.now()
  topic_base = None
  
  if cfg["HASS_ENABLE"]:
    hass = hass_int.HassIntegration()
  else:
    hass = None
  
  mqttclient = mqtt.mqtt_start( hass )
  api = MTECmodbusAPI.MTECmodbusAPI()
  api.connect(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'])

  # Main loop - exit on signal only
  while run_status: 
    now = datetime.now()

    # Config
    if next_read_config <= now:
      pv_config = read_MTEC_data( api, "config" )
      if pv_config:
        topic_base = cfg['MQTT_TOPIC'] + '/' + pv_config["serial_no"]["value"] + '/'
        write_to_MQTT( pv_config, topic_base + 'config/' )
        next_read_config = datetime.now() + timedelta(hours=cfg['REFRESH_CONFIG_H'])
        if hass and not hass.is_initialized:
          hass.initialize( pv_config["serial_no"]["value"] )
      if not topic_base:
        logging.error("Cant retrieve initial config - retry in {}s".format( cfg['REFRESH_NOW_S'] ))
        time.sleep(cfg['REFRESH_NOW_S'])
        continue

    # Now 
    pvdata = read_MTEC_data( api, "now-base" )
    if pvdata:
      write_to_MQTT( pvdata, topic_base + 'now/' )
    if cfg['ENABLE_GRID_DATA']:
      pvdata = read_MTEC_data( api, "now-grid" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now/' )
    if cfg['ENABLE_INVERTER_DATA']:
      pvdata = read_MTEC_data( api, "now-inverter" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now/' )
    if cfg['ENABLE_BACKUP_DATA']:
      pvdata = read_MTEC_data( api, "now-backup" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now/' )
    if cfg['ENABLE_BATTERY_DATA']:
      pvdata = read_MTEC_data( api, "now-battery" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now/' )
    if cfg['ENABLE_PV_DATA']:
      pvdata = read_MTEC_data( api, "now-pv" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now/' )

    # Day
    if next_read_day <= now:
      pvdata = read_MTEC_data( api, "day" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'day/' )
        next_read_day = datetime.now() + timedelta(minutes=cfg['REFRESH_DAY_M'])

    # Total
    if next_read_total <= now:
      pvdata = read_MTEC_data( api, "total" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'total/' )
        next_read_total = datetime.now() + timedelta(minutes=cfg['REFRESH_TOTAL_M'])

    logging.debug("Sleep {}s".format( cfg['REFRESH_NOW_S'] ))
    time.sleep(cfg['REFRESH_NOW_S'])

  # clean up
  if hass:
    hass.send_unregister_info()
  api.disconnect()
  mqtt.mqtt_stop(mqttclient)
  logging.info("Exiting")
 
#---------------------------------------------------
if __name__ == '__main__':
  main()

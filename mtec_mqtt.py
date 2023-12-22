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

# =============================================
# MTEC Modbus read
# Helper to get list of registers to read
def get_register_list( category ):
  if category == "config":
    registers = [ '10000', '10011' ]
  elif category == "now-base":  
    registers = [ '10100', '10105', '11028', '11000', '30258', '11016', '30230', '33000' ] 
  elif category == "now-grid":  
    registers = [ '11015', '10994', '10996', '10998' ]
  elif category == "now-inverter":  
    registers = [ '11009', '11010', '30236', '11011', '11012', '30242', '11013', '11014', '30248', '11032', '11033', '11034', '11035' ]
  elif category == "now-backup":  
    registers = [ '30200', '30201', '30202', '30204', '30210', '30211', '30212', '30214', '30220', '30221', '30222', '30224' ]
  elif category == "now-battery":  
    registers = [ '33001', '30254', '30255', '30256', '33009', '33011', '33013', '33015' ]
  elif category == "now-pv":  
    registers = [ '11038','11039', '11062', '11040', '11041', '11064' ]
  elif category == "day":  
    registers = [ '31000', '31001', '31003', '31004', '31005']
  elif category == "total":  
    registers = [ '31102', '31104', '31108', '31110', '31112']
  else:
    logging.error("Unknown read category: {}".format(category))
    return None              
  return registers

# read data from MTEC modbus
def read_MTEC_data( api, category ):
  logging.info("Reading registers for category: {}".format(category))
  registers = get_register_list( category )
  now = datetime.now()
  data = api.read_modbus_data(registers=registers)
  pvdata = {}
  try:
    pvdata["api_date"] = now.strftime("%Y-%m-%d %H:%M:%S") # Local time of this server

    if category == "config":
      pvdata["serial_no"] = data["10000"]                   # Inverter serial number
      pvdata["firmware_version"] = data["10011"]            # Inverter firmware version

    elif category == "now-base":  
      pvdata["inverter_date"] = data["10100"]               # Time from inverter
      pvdata["inverter_status"] = data["10105"]             # Inverter status 
      pvdata["pv"] = data["11028"]                      # power flow from PV
      pvdata["grid"] = data["11000"]                    # power flow from/to grid
      pvdata["battery"] = data["30258"]                 # power flow from/to battery
      pvdata["inverter"] = data["11016"]                # power flow from/to inverter
      pvdata["backup"] = data["30230"]                  # backup power flow
      pvdata["consumption"] = data["11016"]["value"] - data["11000"]["value"]  # power consumption 
      pvdata["battery_soc"] = data["33000"]           	# battery SOC

    elif category == "now-grid":  
      pvdata["grid_frequency"] = data["11015"]          # grid frequency
      pvdata["grid_a"] = data["10994"]                  # power flow from/to grid, phase A
      pvdata["grid_b"] = data["10996"]                  # power flow from/to grid, phase B
      pvdata["grid_c"] = data["10998"]                  # power flow from/to grid, phase C

    elif category == "now-inverter":  
      pvdata["inverter_voltage_a"] = data["11009"]      # inverter voltage, phase A
      pvdata["inverter_current_a"] = data["11010"]      # inverter current, phase A 
      pvdata["inverter_a"] = data["30236"]              # inverter power, phase A 
      pvdata["inverter_voltage_b"] = data["11011"]      # inverter voltage, phase B
      pvdata["inverter_current_b"] = data["11012"]      # inverter current, phase B
      pvdata["inverter_b"] = data["30242"]              # inverter power, phase B 
      pvdata["inverter_voltage_c"] = data["11013"]      # inverter voltage, phase C 
      pvdata["inverter_current_c"] = data["11014"]      # inverter current, phase C 
      pvdata["inverter_c"] = data["30248"]              # inverter power, phase C 
      pvdata["inverter_temp1"] = data["11032"]          # inverter temperature sensor 1 
      pvdata["inverter_temp2"] = data["11033"]          # inverter temperature sensor 2 
      pvdata["inverter_temp3"] = data["11034"]          # inverter temperature sensor 3 
      pvdata["inverter_temp4"] = data["11035"]          # inverter temperature sensor 4

    elif category == "now-backup":  
      pvdata["backup_voltage_a"] = data["30200"]        # Backup voltage, phase A 
      pvdata["backup_current_a"] = data["30201"]        # Backup current, phase A 
      pvdata["backup_frequency_a"] = data["30202"]      # Backup frequency, phase A 
      pvdata["backup_a"] = data["30204"]                # Backup power, phase A 
      pvdata["backup_voltage_b"] = data["30210"]        # Backup voltage, phase B 
      pvdata["backup_current_b"] = data["30211"]        # Backup current, phase B 
      pvdata["backup_frequency_b"] = data["30212"]      # Backup frequency, phase B 
      pvdata["backup_b"] = data["30214"]                # Backup power, phase B
      pvdata["backup_voltage_c"] = data["30220"]        # Backup voltage, phase C 
      pvdata["backup_current_c"] = data["30221"]        # Backup current, phase C 
      pvdata["backup_frequency_c"] = data["30222"]      # Backup frequency, phase C 
      pvdata["backup_c"] = data["30224"]                # Backup power, phase C

    elif category == "now-battery":  
      pvdata["battery_soh"] = data["33001"]           	# Battery SOH
      pvdata["battery_voltage"] = data["30254"]         # Battery voltage
      pvdata["battery_current"] = data["30255"]         # Battery current
      pvdata["battery_mode"] = data["30256"]            # Battery mode
      pvdata["battery_cell_t_max"] = data["33009"]      # Battery min. cell temperature
      pvdata["battery_cell_t_min"] = data["33011"]      # Battery min. cell temperature
      pvdata["battery_cell_v_max"] = data["33013"]      # Battery max. cell voltage
      pvdata["battery_cell_v_min"] = data["33015"]      # Battery min. cell voltage

    elif category == "now-pv":  
      pvdata["pv_voltage_1"] = data["11038"]             # PV1 voltage 
      pvdata["pv_current_1"] = data["11039"]             # PV1 voltage 
      pvdata["pv_1"] = data["11062"]                     # PV1 power 
      pvdata["pv_voltage_2"] = data["11040"]             # PV2 voltage 
      pvdata["pv_current_2"] = data["11041"]             # PV2 voltage 
      pvdata["pv_2"] = data["11064"]                     # PV2 power 

    elif category == "day":  
      pvdata["PV"] = data["31005"]                      # Energy generated by PV today
      pvdata["grid_feed"] = data["31000"]               # Energy feed to grid today
      pvdata["grid_purchase"] = data["31001"]           # Energy purchased from grid today
      pvdata["battery_charge"] = data["31003"]          # Energy charged to battery total
      pvdata["battery_discharge"] = data["31004"]       # Energy discharged from battery total
      pvdata["consumption"] = data["31005"]["value"] + data["31001"]["value"] + data["31004"]["value"] - data["31000"]["value"] - data["31003"]["value"]  # power consumption 
      pvdata["autarky_rate"] = 100*(1 - (data["31001"]["value"] / pvdata["consumption"])) if pvdata["consumption"]>0 else 0 
      pvdata["own_consumption_rate"] = 100*(1-data["31000"]["value"] / data["31005"]["value"]) if data["31005"]["value"]>0 else 0

    elif category == "total":  
      pvdata["PV"] = data["31112"]                      # Energy generated by PV total
      pvdata["grid_feed"] = data["31102"]               # Energy feed to grid total
      pvdata["grid_purchase"] = data["31104"]           # Energy purchased from grid total
      pvdata["battery_charge"] = data["31108"]          # Energy charged to battery total
      pvdata["battery_discharge"] = data["31110"]       # Energy discharged from battery total
      pvdata["consumption"] = data["31112"]["value"] + data["31104"]["value"] + data["31110"]["value"] - data["31102"]["value"] - data["31108"]["value"]  # power consumption 
      pvdata["autarky_rate"] = 100*(1 - (data["31104"]["value"] / pvdata["consumption"])) if pvdata["consumption"]>0 else 0
      pvdata["own_consumption_rate"] = 100*(1-data["31102"]["value"] / data["31112"]["value"]) if data["31112"]["value"]>0 else 0
  except Exception as e:
    logging.warning("Retrieved Modbus data is incomplete: {}".format(str(e)))
    return None
  return pvdata

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

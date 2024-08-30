#!/usr/bin/env python3
"""
MQTT server for M-TEC Energybutler reading modbus data
(c) 2024 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from mtecmqtt.config import cfg, register_map
from datetime import datetime, timedelta
import time
import signal
from mtecmqtt.mqtt import mqtt_start, mqtt_stop, mqtt_publish
from mtecmqtt.MTECmodbusAPI import MTECmodbusAPI
from mtecmqtt.hass_int import HassIntegration

#----------------------------------
def signal_handler(signal_number, frame):
  global run_status
  logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
  run_status = False

# =============================================
# read data from MTEC modbus
def read_MTEC_data( api, group ):
  logging.info("Reading registers for group: {}".format(group))
  registers = api.get_register_list( group )
  now = datetime.now()
  data = api.read_modbus_data(registers=registers)
  pvdata = {}
  try: # assign all data
    for register in registers:
      item = register_map[register]
      if item["mqtt"]:
        if register.isnumeric():  
          pvdata[item["mqtt"]] = data[register]
        else: # non-numeric registers are deemed to be calculated pseudo-registers  
          if register == "consumption":  
            pvdata[item["mqtt"]] = data["11016"]["value"] - data["11000"]["value"]  # power consumption 
          elif register == "consumption-day":
            pvdata[item["mqtt"]] = data["31005"]["value"] + data["31001"]["value"] + data["31004"]["value"] - data["31000"]["value"] - data["31003"]["value"]  # power consumption 
          elif register == "autarky-day":
            pvdata[item["mqtt"]] = 100*(1 - (data["31001"]["value"] / pvdata["consumption_day"])) if pvdata["consumption_day"]>0 else 0
          elif register == "ownconsumption-day":
            pvdata[item["mqtt"]] = 100*(1-data["31000"]["value"] / data["31005"]["value"]) if data["31005"]["value"]>0 else 0
          elif register == "consumption-total":
            pvdata[item["mqtt"]] = data["31112"]["value"] + data["31104"]["value"] + data["31110"]["value"] - data["31102"]["value"] - data["31108"]["value"]  # power consumption 
          elif register == "autarky-total":
            pvdata[item["mqtt"]] = 100*(1 - (data["31104"]["value"] / pvdata["consumption_total"])) if pvdata["consumption_total"]>0 else 0
          elif register == "ownconsumption-total":
            pvdata[item["mqtt"]] = 100*(1-data["31102"]["value"] / data["31112"]["value"]) if data["31112"]["value"]>0 else 0
          elif register == "api-date":    
            pvdata[item["mqtt"]] = now.strftime("%Y-%m-%d %H:%M:%S") # Local time of this server
          else:  
            logging.warning("Unknown calculated pseudo-register: {}".format(register))

          if isinstance(pvdata[item["mqtt"]], float) and pvdata[item["mqtt"]] < 0: # Avoid to report negative values, which might occur in some edge cases  
            pvdata[item["mqtt"]] = 0 
 
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
    mqtt_publish( topic, payload )

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
  now_ext_idx = 0
  topic_base = None

  api = MTECmodbusAPI()
  connected = api.connect(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'])
  if not connected:
    # try alternative port (defaults to 502)
    connected = api.connect(ip_addr=cfg['MODBUS_IP'], port=cfg.get('MODBUS_PORT2',"502"), slave=cfg['MODBUS_SLAVE'])
    if not connected:    
      logging.fatal( "Can't connect to MODBUS server: {}:{} slave {}".format(cfg['MODBUS_IP'], cfg['MODBUS_PORT'], cfg['MODBUS_SLAVE']) )
      return

  if cfg["HASS_ENABLE"]:
    hass = HassIntegration()
  else:
    hass = None
  mqttclient = mqtt_start( hass )

  # Initialize  
  pv_config = None
  while run_status and not pv_config:
    pv_config = read_MTEC_data( api, "config" )
    if not pv_config:
      logging.warning("Cant retrieve initial config - retry in 10 s")
      time.sleep(10)
  
  if not pv_config:
    logging.fatal("Cant retrieve initial config.")
    return
  
  topic_base = cfg['MQTT_TOPIC'] + '/' + pv_config["serial_no"]["value"] + '/'  
  if hass and not hass.is_initialized:
    hass.initialize( pv_config["serial_no"]["value"] )

  # Main loop - exit on signal only
  while run_status: 
    now = datetime.now()

    # Now base
    pvdata = read_MTEC_data( api, "now-base" )
    if pvdata:
      write_to_MQTT( pvdata, topic_base + 'now-base/' )

    # Now extended - read groups in a round robin - one per loop
    if now_ext_idx == 0:
      pvdata = read_MTEC_data( api, "now-grid" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now-grid/' )
    elif now_ext_idx == 1:
      pvdata = read_MTEC_data( api, "now-inverter" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now-inverter/' )
    elif now_ext_idx == 2:
      pvdata = read_MTEC_data( api, "now-backup" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now-backup/' )
    elif now_ext_idx == 3:
      pvdata = read_MTEC_data( api, "now-battery" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now-battery/' )
    elif now_ext_idx == 4:
      pvdata = read_MTEC_data( api, "now-pv" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'now-pv/' )
    
    if now_ext_idx >= 4:
      now_ext_idx = 0
    else:  
      now_ext_idx += 1

    # Day
    if next_read_day <= now:
      pvdata = read_MTEC_data( api, "day" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'day/' )
        next_read_day = datetime.now() + timedelta(seconds=cfg['REFRESH_DAY'])

    # Total
    if next_read_total <= now:
      pvdata = read_MTEC_data( api, "total" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'total/' )
        next_read_total = datetime.now() + timedelta(seconds=cfg['REFRESH_TOTAL'])

    # Config
    if next_read_config <= now:
      pvdata = read_MTEC_data( api, "config" )
      if pvdata:
        write_to_MQTT( pvdata, topic_base + 'config/' )
        next_read_config = datetime.now() + timedelta(seconds=cfg['REFRESH_CONFIG'])

    logging.debug("Sleep {}s".format( cfg['REFRESH_NOW'] ))
    time.sleep(cfg['REFRESH_NOW'])

  # clean up
  if hass:
    hass.send_unregister_info()
  api.disconnect()
  mqtt_stop(mqttclient)
  logging.info("Exiting")
 
#---------------------------------------------------
if __name__ == '__main__':
  main()

#!/usr/bin/env python3
"""
MQTT server for M-TEC Energybutler reading modbus data
"""
from config import cfg
import logging
import time
import signal
import MTECmodbusAPI

try:
  import paho.mqtt.client as mqttcl
  import paho.mqtt.publish as publish
except Exception as e:
  logging.warning("MQTT not set up because of: {}".format(e))

run_status = True  

#----------------------------------
def signal_handler(signal_number, frame):
  global run_status
  logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
  run_status = False
    
# ============ MQTT ================
def on_mqtt_connect(mqttclient, userdata, flags, rc):
  logging.info("Connected to MQTT broker")

def on_mqtt_message(mqttclient, userdata, message):
  try:
    msg = message.payload.decode("utf-8")
    topic = message.topic.split("/")
  except Exception as e:
    logging.warning("Error while handling MQTT message: {}".format(str(e)))

def mqtt_start(): 
  try: 
    client = mqttcl.Client()
    client.username_pw_set(cfg['MQTT_LOGIN'], cfg['MQTT_PASSWORD']) 
    client.connect(cfg['MQTT_SERVER'], cfg['MQTT_PORT'], keepalive = 60) 
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.loop_start()
    logging.info('MQTT server started')
    return client
  except Exception as e:
    logging.warning("Couldn't start MQTT: {}".format(str(e)))
    return None

def mqtt_stop(client):
  try: 
    client.loop_stop()
    logging.info('MQTT server stopped')
  except Exception as e:
    logging.warning("Couldn't stop MQTT: {}".format(str(e)))

def mqtt_publish( topic, payload ):  
  auth = {
    'username': cfg['MQTT_LOGIN'],
    'password': cfg['MQTT_PASSWORD'] 
  }  
  logging.debug("Publish MQTT command {}: {}".format(topic, payload))
  try:
    publish.single(topic, payload=payload, hostname=cfg['MQTT_SERVER'], port=cfg['MQTT_PORT'], auth=auth)
  except Exception as e:
    logging.error("Could't send MQTT command: {}".format(str(e)))

# =============================================

# read data from MTEC modbus
def read_MTEC_data( addresses ):
  data = MTECmodbusAPI.read_modbus_data(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], 
                                        slave=cfg['MODBUS_SLAVE'], addresses=addresses)
  pvdata = {}
  try:
    pvdata["day_production"] = data["11018"]              # Energy produced by the PV today
    pvdata["total_production"] = data["11020"]            # Energy produced by the PV in total
    pvdata["current_PV"] = data["11028"]                  # Current flow from PV
    pvdata["current_grid"] = data["11000"]                # Current flow from/to grid
    pvdata["current_battery"] = data["30258"]             # Current flow from/to battery
    pvdata["current_inverter"] = data["11016"]            # Current flow from/to inverter
    pvdata["current_house"] = data["11016"]["value"] - data["11000"]["value"]  # Current flow to house (house consumption)
    pvdata["current_battery_SOC"] = data["33000"]         # Current battery SOC
    pvdata["inverter_status"] = data["10105"]             # Inverter status
  except Exception as e:
    logging.warning("Retrieved Modbus data is incomplete: {}".format(str(e)))
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
    logging.info("- {}: {}".format(topic, str(payload)))
#    mqtt_publish( topic, payload )

#==========================================
def main():
  global run_status

  # Initializaion
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)
  logging.basicConfig()
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)
  logging.info("Starting")

  addresses = [ '10105', '11000', '11016', '11018', '11020', '11028', '30258', '33000' ]
  mqttclient = mqtt_start()

  while run_status: # and mqttclient
    pvdata = read_MTEC_data(addresses=addresses)
    if pvdata:
      write_to_MQTT( pvdata, cfg['MQTT_TOPIC'] + '/' )
    logging.debug("Sleep {}s".format( cfg['POLL_FREQUENCY'] ))
    time.sleep(cfg['POLL_FREQUENCY'])

  mqtt_stop(mqttclient)
  logging.info("Stopped")

if __name__ == '__main__':
  main()

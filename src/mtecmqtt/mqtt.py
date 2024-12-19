#!/usr/bin/env python3
"""
MQTT client base implemantation
(c) 2024 by Christian Rödel 
"""
import logging
from mtecmqtt.config import cfg
import time

try:
  import paho.mqtt.client as mqttcl
  import paho.mqtt.publish as publish
except Exception as e:
  logging.warning("MQTT not set up because of: {}".format(e))
    
# ============ MQTT ================
def on_mqtt_connect(mqttclient, userdata, flags, rc, prop):
  if rc == 0:
    logging.info("Connected to MQTT broker")
  else:
    logging.error("Error while connecting to MQTT broker: rc={}".format(rc))

def on_mqtt_disconnect(mqttclient, userdata, rc):
  logging.warning("MQTT broker disconnected: rc={}".format(rc))
  
def on_mqtt_subscribe(mqttclient, userdata, mid, granted_qos):
  logging.info("MQTT broker subscribed to mid {}".format(mid))

def on_mqtt_message(mqttclient, userdata, message):
  try:
    msg = message.payload.decode("utf-8")
    topic = message.topic.split("/")
    if msg == "online" and userdata:
      gracetime = cfg.get("HASS_BIRTH_GRACETIME", 15)
      logging.info("Received HASS online message. Sending discovery info in {} sec".format(gracetime))
      time.sleep(gracetime) # dirty workaround: hass requires some grace period for being ready to receive discovery info
      userdata.send_discovery_info()
  except Exception as e:
    logging.warning("Error while handling MQTT message: {}".format(str(e)))

def mqtt_start( hass=None ): 
  try: 
    client = mqttcl.Client(mqttcl.CallbackAPIVersion.VERSION2)
    client.user_data_set(hass) # register home automation instance
    client.username_pw_set(cfg['MQTT_LOGIN'], cfg['MQTT_PASSWORD']) 
    client.on_connect = on_mqtt_connect
    client.on_disconnect = on_mqtt_disconnect
    client.on_message = on_mqtt_message
    client.on_subscribe = on_mqtt_subscribe
    client.connect(cfg['MQTT_SERVER'], cfg['MQTT_PORT'], keepalive = 60) 
    if hass:
      client.subscribe(cfg["HASS_BASE_TOPIC"]+"/status", qos=0)
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
  if cfg['MQTT_DISABLE']: # Don't do anything - just logg
    logging.info("- {}: {}".format(topic, str(payload)))
  else:  
    auth = { 'username': cfg['MQTT_LOGIN'], 'password': cfg['MQTT_PASSWORD'] }  
    logging.debug("- {}: {}".format(topic, str(payload)))
    try:
      publish.single(topic, payload=payload, hostname=cfg['MQTT_SERVER'], port=cfg['MQTT_PORT'], auth=auth)
    except Exception as e:
      logging.error("Could't send MQTT command: {}".format(str(e)))

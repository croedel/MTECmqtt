#!/usr/bin/env python3
"""
Auto discovery for home assistant
(c) 2024 by Christian Rödel 
"""

from mtecmqtt.config import cfg, register_map
import logging
import json
from mtecmqtt.mqtt import mqtt_publish

#---------------------------------------------------
class HassIntegration:
  # Custom automations
  buttons = [
    # name                        unique_id                   payload_press              
#    [ "Set general mode",         "MTEC_load_battery_btn",    "load_battery_from_grid" ],
  ]

  #-------------------------------------------------
  def __init__(self):
    self.serial_no = None
    self.is_initialized = False
    self.devices_array=[]

  #---------------------------------------------------
  def initialize( self, serial_no ):
    self.serial_no = serial_no
    self.device_info = { 
      "identifiers": [ self.serial_no ],
      "name": "MTEC Energybutler", 
      "manufacturer": "MTEC", 
      "model": "Energybutler",
      "via_device": "MTECmqtt" 
    }  
    self.devices_array.clear()
    self._build_devices_array()
    self._build_automation_array()
    self.send_discovery_info()
    self.is_initialized = True  

  #---------------------------------------------------
  def send_discovery_info( self ):
    logging.info('Sending home assistant discovery info')
    for device in self.devices_array:
      mqtt_publish( topic=device[0], payload=device[1] ) 

  #---------------------------------------------------
  def send_unregister_info( self ):
    logging.info('Sending info to unregister from home assistant')
    for device in self.devices_array:
      mqtt_publish( topic=device[0], payload="" ) 

  #---------------------------------------------------
  def _build_automation_array( self ):
    # Buttons
    for item in self.buttons:
      data_item = { 
        "name": item[0], 
        "unique_id": item[1], 
        "payload_press": item[2],
        "command_topic": "MTEC/" + self.serial_no + "/automations/command",
        "device": self.device_info
      }
      topic = cfg["HASS_BASE_TOPIC"] + "/button/" + item[1] + "/config"
      self.devices_array.append( [topic, json.dumps(data_item)] )  

  #---------------------------------------------------
  # build discovery data for devices
  def _build_devices_array( self ):
    for register, item in register_map.items():
      # Do registration if there is a "hass_" config entry
      do_hass_registration = False
      for key in item.keys():
        if "hass_" in key:
          do_hass_registration = True
          break

      if item["group"] and do_hass_registration: 
        if ( (item["group"] in ["now-base", "day", "total", "config"]) or 
          (item["group"]=="now-grid" and cfg['ENABLE_GRID_DATA']) or
          (item["group"]=="now-inverter" and cfg['ENABLE_INVERTER_DATA']) or
          (item["group"]=="now-backup" and cfg['ENABLE_BACKUP_DATA']) or
          (item["group"]=="now-battery" and cfg['ENABLE_BATTERY_DATA']) or
          (item["group"]=="now-pv" and cfg['ENABLE_PV_DATA']) 
        ):
          component_type = item.get("hass_component_type", "sensor")
          if component_type == "sensor":
            self._append_sensor(item)   
          if component_type == "binary_sensor":
            self._append_binary_sensor(item)   

  #---------------------------------------------------
  def _append_sensor( self, item ):               
    data_item = { 
      "name": item["name"], 
      "unique_id": "MTEC_" + item["mqtt"], 
      "unit_of_measurement": item["unit"],
      "state_topic": "MTEC/" + self.serial_no + "/" + item["group"] + "/" + item["mqtt"],
      "device": self.device_info
    }
    if item.get("hass_device_class"):
      data_item["device_class"] = item["hass_device_class"] 
    if item.get("hass_value_template"):
      data_item["value_template"] = item["hass_value_template"] 
    if item.get("hass_state_class"):
      data_item["state_class"] = item["hass_state_class"] 

    topic = cfg["HASS_BASE_TOPIC"] + "/sensor/" + "MTEC_" + item["mqtt"] + "/config"
    self.devices_array.append( [topic, json.dumps(data_item)] )  

#---------------------------------------------------
  def _append_binary_sensor( self, item ):               
    data_item = { 
      "name": item["name"], 
      "unique_id": "MTEC_" + item["mqtt"], 
      "state_topic": "MTEC/" + self.serial_no + "/" + item["group"] + "/" + item["mqtt"],
      "device": self.device_info
    }
    if item.get("hass_device_class"):
      data_item["device_class"] = item["hass_device_class"] 
    if item.get("hass_payload_on"):
      data_item["payload_on"] = item["hass_payload_on"] 
    if item.get("hass_payload_off"):
      data_item["payload_off"] = item["hass_payload_off"] 

    topic = cfg["HASS_BASE_TOPIC"] + "/binary_sensor/" + "MTEC_" + item["mqtt"] + "/config"
    self.devices_array.append( [topic, json.dumps(data_item)] )  

#---------------------------------------------------
# Testcode only
def main():
  hass = HassIntegration()
  hass.initialize( "my_serial_number" )

  for i in hass.devices_array:
    topic = i[0]
    data = i[1]
    logging.info( "- {}: {}".format(topic, data) )

#---------------------------------------------------
if __name__ == '__main__':
  main()

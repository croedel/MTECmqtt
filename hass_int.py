#!/usr/bin/env python3
"""
Auto discovery for home assistant
(c) 2024 by Christian Rödel 
"""

from config import cfg, register_map
import logging
import json
import mqtt

#---------------------------------------------------
class HassIntegration:
  # Custom automations
  buttons = [
    # name                        unique_id                   payload_press              
#    [ "Set general mode",         "MTEC_load_battery_btn",    "load_battery_from_grid" ],
  ]
  switches = [
    # name                        unique_id                     
#    [ "Load battery from grid",   "MTEC_load_battery_btn" ],
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
      "sw_version": "V0.1" 
    }  
    self.devices_array.clear()
    self._build_sensor_array()
    self._build_automation_array()
    self.send_discovery_info()
    self.is_initialized = True  

  #---------------------------------------------------
  def send_discovery_info( self ):
    logging.info('Sending home assistant discovery info')
    for device in self.devices_array:
      mqtt.mqtt_publish( topic=device[0], payload=device[1] ) 

  #---------------------------------------------------
  def send_unregister_info( self ):
    logging.info('Sending info to unregister from home assistant')
    for device in self.devices_array:
      mqtt.mqtt_publish( topic=device[0], payload="" ) 

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

    # Switches
    for item in self.switches:
      data_item = { 
        "name": item[0], 
        "unique_id": item[1], 
        "payload_on": "ON",
        "payload_off": "OFF",
        "state_on": "ON",
        "state_off": "OFF",
        "state_topic": "MTEC/" + self.serial_no + "/automations/" + item[1],
        "command_topic": "MTEC/" + self.serial_no + "/automations/" + item[1] + "/command",
        "device": self.device_info
      }
      topic = cfg["HASS_BASE_TOPIC"] + "/switch/" + item[1] + "/config"
      self.devices_array.append( [topic, json.dumps(data_item)] )  

  #---------------------------------------------------
  def _build_sensor_array( self ):
    # build sensor registration
    for register, item in register_map.items():
      if item["group"] and item.get("hass_state_class"): # Do not announce items without group or hass_state_class
        if ( (item["group"] in ["now-base", "day", "total"]) or 
          (item["group"]=="now-grid" and cfg['ENABLE_GRID_DATA']) or
          (item["group"]=="now-inverter" and cfg['ENABLE_INVERTER_DATA']) or
          (item["group"]=="now-backup" and cfg['ENABLE_BACKUP_DATA']) or
          (item["group"]=="now-battery" and cfg['ENABLE_BATTERY_DATA']) or
          (item["group"]=="now-pv" and cfg['ENABLE_PV_DATA']) 
        ):        
          data_item = { 
            "name": item["name"], 
            "unique_id": "MTEC_" + item["mqtt"], 
            "device_class": item["hass_device_class"], 
            "unit_of_measurement": item["unit"],
            "value_template": item["hass_value_template"], 
            "state_class": item["hass_state_class"], 
            "state_topic": "MTEC/" + self.serial_no + "/" + item["group"] + "/" + item["mqtt"],
            "device": self.device_info
          }
          topic = cfg["HASS_BASE_TOPIC"] + "/sensor/" + "MTEC_" + item["mqtt"] + "/config"
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

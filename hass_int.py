#!/usr/bin/env python3
"""
Auto discovery for home assistant
(c) 2023 by Christian Rödel 
"""

import logging
import json
from config import cfg
import mqtt

#---------------------------------------------------
class HassIntegration:
  # list of sensors which shall be registered at home assistant
  sensors = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Battery SOC",            "MTEC_cBatterySOC", "battery",    "%",  "{{ value }}",  "measurement",  "current/battery_SOC" ],
    [ "Inverter status",        "MTEC_cInvStat",    "enum",       None, "{{ value }}",  "measurement",  "current/inverter_status" ],
    [ "Current PV",             "MTEC_cPV",         "power",      "W",  "{{ value }}",  "measurement",  "current/PV" ],
    [ "Current Grid",           "MTEC_cGrid",       "power",      "W",  "{{ value }}",  "measurement",  "current/grid" ],
    [ "Current Battery",        "MTEC_cBatt",       "power",      "W",  "{{ value }}",  "measurement",  "current/battery" ],
    [ "Current Inverter",       "MTEC_cInv",        "power",      "W",  "{{ value }}",  "measurement",  "current/inverter" ],
    [ "Current Backup",         "MTEC_cBack",       "power",      "W",  "{{ value }}",  "measurement",  "current/backup" ],
    [ "Current Consumption",    "MTEC_cCons",       "power",      "W",  "{{ value }}",  "measurement",  "current/consumption" ],
#    [ "API date",               "MTEC_APIdate",     "timestamp",  None,   "{{ strptime(value, '%Y-%m-%d %H:%M:%S').timestamp() | timestamp_local }}", None, "current/api_date" ],
#    [ "Inverter date",          "MTEC_Invdate",     "timestamp",  None,   "{{ strptime(value, '%y-%m-%d %H:%M:%S').timestamp() | timestamp_local }}", None, "current/inverter_date" ],

    [ "PV (day)",               "MTEC_dPV",         "energy",     "kWh",  "{{ value }}",  "total_increasing",  "day/PV" ],
    [ "Grid feed (day)",        "MTEC_dGridFeed",   "energy",     "kWh",  "{{ value }}",  "total_increasing",  "day/grid_feed" ],
    [ "Grid purchase (day)",    "MTEC_dGridPurchase", "energy",   "kWh",  "{{ value }}",  "total_increasing",  "day/grid_purchase" ],
    [ "Battery charge (day)",   "MTEC_dBattCharge",  "energy",    "kWh",  "{{ value }}",  "total_increasing",  "day/battery_charge" ],
    [ "Battery discharge (day)","MTEC_dBattDischarge", "energy",  "kWh",  "{{ value }}",  "total_increasing",  "day/battery_discharge" ],
    [ "Consumption (day)",      "MTEC_dCons",         "energy",   "kWh",  "{{ value }}",  "total_increasing",  "day/consumption" ],
    [ "Autarky rate (day)",     "MTEC_dAutarky",     "power_factor", "%",  "{{ value }}",  "measurement",       "day/autarky_rate" ],
    [ "Own consumption rate (day)", "MTEC_dOwnCons", "power_factor", "%",  "{{ value }}",  "measurement",       "day/own_consumption_rate" ],

    [ "PV (total)",               "MTEC_tPV",         "energy",     "kWh",  "{{ value }}",  "total_increasing",  "total/PV" ],
    [ "Grid feed (total)",        "MTEC_tGridFeed",   "energy",     "kWh",  "{{ value }}",  "total_increasing",  "total/grid_feed" ],
    [ "Grid purchase (total)",    "MTEC_tGridPurchase", "energy",   "kWh",  "{{ value }}",  "total_increasing",  "total/grid_purchase" ],
    [ "Battery charge (total)",   "MTEC_tBattCharge",  "energy",    "kWh",  "{{ value }}",  "total_increasing",  "total/battery_charge" ],
    [ "Battery discharge (total)","MTEC_tBattDischarge", "energy",  "kWh",  "{{ value }}",  "total_increasing",  "total/battery_discharge" ],
    [ "Consumption (total)",      "MTEC_tCons",         "energy",   "kWh",  "{{ value }}",  "total_increasing",  "total/consumption" ],
    [ "Autarky rate (total)",     "MTEC_tAutarky",     "power_factor", "%",  "{{ value }}",  "measurement",       "total/autarky_rate" ],
    [ "Own consumption rate (total)", "MTEC_tOwnCons", "power_factor", "%",  "{{ value }}",  "measurement",       "total/own_consumption_rate" ],
  ]

  #-------------------------------------------------
  def __init__(self):
    self.serial_no = None
    self.is_initialized = False
    self.sensor_array= []

  #---------------------------------------------------
  def initialize( self, serial_no ):
    self.serial_no = serial_no
    self._build_sensor_array()
    self.send_discovery_info()
    self.is_initialized = True  

  #---------------------------------------------------
  def send_discovery_info( self ):
    logging.info('Sending home assistant discovery info')
    for sensor in self.sensor_array:
      mqtt.mqtt_publish( topic=sensor[0], payload=sensor[1] ) 

  #---------------------------------------------------
  def send_unregister_info( self ):
    logging.info('Sending info to unregister from home assistant')
    for sensor in self.sensor_array:
      mqtt.mqtt_publish( topic=sensor[0], payload="" ) 

  #---------------------------------------------------
  def _build_sensor_array( self ):
    self.sensor_array.clear()
    # MTEC device info
    device = { 
      "identifiers": [ self.serial_no ],
      "name": "MTEC Energybutler", 
      "manufacturer": "MTEC", 
      "model": "Energybutler",
      "sw_version": "V0.1" 
    }  

    #individual sensors
    for item in self.sensors:
      data_item = { 
        "name": item[0], 
        "unique_id": item[1], 
        "device_class": item[2], 
        "unit_of_measurement": item[3],
        "value_template": item[4], 
        "state_class": item[5], 
        "state_topic": "MTEC/" + self.serial_no + "/" + item[6],
        "device": device
      }
      topic = cfg["HASS_BASE_TOPIC"] + "/sensor/" + item[1] + "/config"
      self.sensor_array.append( [topic, json.dumps(data_item)] )  

#---------------------------------------------------
# Testcode only
def main():
  hass = HassIntegration()
  hass.initialize( "my_serial_number" )
  for i in hass.sensor_array:
    topic = i[0]
    data = i[1]
    logging.info( "- {}: {}".format(topic, data) )

#---------------------------------------------------
if __name__ == '__main__':
  main()

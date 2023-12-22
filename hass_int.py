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
  # base list of sensors which shall be registered at home assistant
  sensors_base = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Battery SOC",            "MTEC_BatterySOC",  "battery",    "%",  "{{ value }}",  "measurement",  "now/battery_soc" ],
    [ "Inverter status",        "MTEC_InvStat",     "enum",       None, "{{ value }}",  "measurement",  "now/inverter_status" ],
    [ "PV (now)",               "MTEC_PV",          "power",      "W",  "{{ value }}",  "measurement",  "now/PV" ],
    [ "Grid (now)",             "MTEC_Grid",        "power",      "W",  "{{ value }}",  "measurement",  "now/grid" ],
    [ "Battery (now)",          "MTEC_Batt",        "power",      "W",  "{{ value }}",  "measurement",  "now/battery" ],
    [ "Inverter (now)",         "MTEC_Inv",         "power",      "W",  "{{ value }}",  "measurement",  "now/inverter" ],
    [ "Backup (now)",           "MTEC_Back",        "power",      "W",  "{{ value }}",  "measurement",  "now/backup" ],
    [ "Consumption (now)",      "MTEC_Cons",        "power",      "W",  "{{ value }}",  "measurement",  "now/consumption" ],
#    [ "API date",               "MTEC_APIdate",     "timestamp",  None,   "{{ strptime(value, '%Y-%m-%d %H:%M:%S').timestamp() | timestamp_local }}", None, "now/api_date" ],
#    [ "Inverter date",          "MTEC_Invdate",     "timestamp",  None,   "{{ strptime(value, '%y-%m-%d %H:%M:%S').timestamp() | timestamp_local }}", None, "now/inverter_date" ],

    [ "PV (day)",               "MTEC_dPV",         "energy",     "kWh",  "{{ value }}",  "total_increasing",  "day/pv" ],
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

  sensors_grid = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Grid frequency",         "MTEC_Grid_f",      "frequency",  "Hz", "{{ value }}",  "measurement",  "now/grid_frequency" ],
    [ "Grid phase A",           "MTEC_Grid_a",      "power",      "W",  "{{ value }}",  "measurement",  "now/grid_a" ],
    [ "Grid phase B",           "MTEC_Grid_b",      "power",      "W",  "{{ value }}",  "measurement",  "now/grid_b" ],
    [ "Grid phase C",           "MTEC_Grid_c",      "power",      "W",  "{{ value }}",  "measurement",  "now/grid_c" ],
  ]

  sensors_inverter = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Inverter voltage phase A",  "MTEC_Inv_v_a",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/inverter_voltage_a" ],
    [ "Inverter current phase A",  "MTEC_Inv_c_a",  "current",    "A",  "{{ value }}",  "measurement",  "now/inverter_current_a" ],
    [ "Inverter power phase A",    "MTEC_Inv_p_a",  "power",      "W",  "{{ value }}",  "measurement",  "now/inverter_a" ],
    [ "Inverter voltage phase B",  "MTEC_Inv_v_b",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/inverter_voltage_b" ],
    [ "Inverter current phase B",  "MTEC_Inv_c_b",  "current",    "A",  "{{ value }}",  "measurement",  "now/inverter_current_b" ],
    [ "Inverter power phase B",    "MTEC_Inv_p_b",  "power",      "W",  "{{ value }}",  "measurement",  "now/inverter_b" ],
    [ "Inverter voltage phase C",  "MTEC_Inv_v_c",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/inverter_voltage_c" ],
    [ "Inverter current phase C",  "MTEC_Inv_c_c",  "current",    "A",  "{{ value }}",  "measurement",  "now/inverter_current_c" ],
    [ "Inverter power phase C",    "MTEC_Inv_p_c",  "power",      "W",  "{{ value }}",  "measurement",  "now/inverter_c" ],
    [ "Inverter temp 1",           "MTEC_Inv_t1",   "temperature", "°C", "{{ value }}", "measurement",  "now/inverter_temp1" ],
    [ "Inverter temp 2",           "MTEC_Inv_t2",   "temperature", "°C", "{{ value }}", "measurement",  "now/inverter_temp2" ],
    [ "Inverter temp 3",           "MTEC_Inv_t3",   "temperature", "°C", "{{ value }}", "measurement",  "now/inverter_temp3" ],
    [ "Inverter temp 4",           "MTEC_Inv_t4",   "temperature", "°C", "{{ value }}", "measurement",  "now/inverter_temp4" ],
  ]

  sensors_backup = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Backup voltage phase A",  "MTEC_Back_v_a",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/backup_voltage_a" ],
    [ "Backup current phase A",  "MTEC_Back_c_a",  "current",    "A",  "{{ value }}",  "measurement",  "now/backup_current_a" ],
    [ "Backup power phase A",    "MTEC_Back_p_a",  "power",      "W",  "{{ value }}",  "measurement",  "now/backup_a" ],
    [ "Backup frequency phase A", "MTEC_Back_f_a", "frequency",  "Hz", "{{ value }}",  "measurement",  "now/backup_frequency_a" ],
    [ "Backup voltage phase B",  "MTEC_Back_v_b",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/backup_voltage_b" ],
    [ "Backup current phase B",  "MTEC_Back_c_b",  "current",    "A",  "{{ value }}",  "measurement",  "now/backup_current_b" ],
    [ "Backup power phase B",    "MTEC_Back_p_b",  "power",      "W",  "{{ value }}",  "measurement",  "now/backup_b" ],
    [ "Backup frequency phase B", "MTEC_Back_f_b", "frequency",  "Hz", "{{ value }}",  "measurement",  "now/backup_frequency_b" ],
    [ "Backup voltage phase C",  "MTEC_Back_v_c",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/backup_voltage_c" ],
    [ "Backup current phase C",  "MTEC_Back_c_c",  "current",    "A",  "{{ value }}",  "measurement",  "now/backup_current_c" ],
    [ "Backup power phase C",    "MTEC_Back_p_c",  "power",      "W",  "{{ value }}",  "measurement",  "now/backup_c" ],
    [ "Backup frequency phase C", "MTEC_Back_f_c", "frequency",  "Hz", "{{ value }}",  "measurement",  "now/backup_frequency_c" ],
  ]

  sensors_battery = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "Battery SOH",            "MTEC_BatterySOH",  "battery",    "%",  "{{ value }}",  "measurement",  "now/battery_soh" ],
    [ "Battery voltage",        "MTEC_Battery_v",   "voltage",    "V",  "{{ value }}",  "measurement",  "now/battery_voltage" ],
    [ "Battery current",        "MTEC_Battery_c",   "current",    "A",  "{{ value }}",  "measurement",  "now/battery_current" ],
    [ "Battery mode",           "MTEC_Battery_mode", "enum",      None, "{{ value }}",  "measurement",  "now/battery_mode" ],
    [ "Battery cell temp max.", "MTEC_Cell_t_max",   "temperature", "°C", "{{ value }}", "measurement",  "now/battery_cell_t_max" ],
    [ "Battery cell temp min.", "MTEC_Cell_t_min",   "temperature", "°C", "{{ value }}", "measurement",  "now/battery_cell_t_min" ],
    [ "Battery cell voltage max.", "MTEC_Cell_v_max", "voltage",    "V",  "{{ value }}",  "measurement",  "now/battery_cell_v_max" ],
    [ "Battery cell voltage min.", "MTEC_Cell_v_min", "voltage",    "V",  "{{ value }}",  "measurement",  "now/battery_cell_v_min" ],
  ]

  sensors_pv = [
    # name                      unique_id           device_class  unit  value_template  state_class     state_topic
    [ "PV voltage string 1",  "MTEC_PV_v_1",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/pv_voltage_1" ],
    [ "PV current string 1",  "MTEC_PV_c_1",  "current",    "A",  "{{ value }}",  "measurement",  "now/pv_current_1" ],
    [ "PV power string 1",    "MTEC_PV_p_1",  "power",      "W",  "{{ value }}",  "measurement",  "now/pv_1" ],
    [ "PV voltage string 2",  "MTEC_PV_v_2",  "voltage",    "V",  "{{ value }}",  "measurement",  "now/pv_voltage_2" ],
    [ "PV current string 2",  "MTEC_PV_c_2",  "current",    "A",  "{{ value }}",  "measurement",  "now/pv_current_2" ],
    [ "PV power string 2",    "MTEC_PV_p_2",  "power",      "W",  "{{ value }}",  "measurement",  "now/pv_2" ],
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

    # build sensor registration
    sensors = self.sensors_base
    if cfg['ENABLE_GRID_DATA']:
      sensors.extend(self.sensors_grid)
    if cfg['ENABLE_INVERTER_DATA']:
      sensors.extend(self.sensors_inverter)
    if cfg['ENABLE_BACKUP_DATA']:
      sensors.extend(self.sensors_backup)
    if cfg['ENABLE_BATTERY_DATA']:
      sensors.extend(self.sensors_battery)
    if cfg['ENABLE_PV_DATA']:
      sensors.extend(self.sensors_pv)

    for item in sensors:
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

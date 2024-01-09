#!/usr/bin/env python3
"""
This is a test utility for MTECmodbusapi.
(c) 2023 by Christian Rödel 
"""
import logging
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from config import cfg, register_map, register_groups
import MTECmodbusAPI

#-------------------------------
def read_register(api):
  print( "-------------------------------------" )
  register = input("Register: ")
  data = api.read_modbus_data( registers=[register] )
  if data: 
    item = data.get(register)
    print("Register {} ({}): {} {}".format(register, item["name"], item["value"], item["unit"]))

#-------------------------------
def read_register_group(api):
  print( "-------------------------------------" )
  line = "Groups: "
  for g in sorted(register_groups):
    line += g + ", "  
  print( line + "all" )

  group = input("Register group (or RETURN for all): ")
  if group=="" or group=="all":
    registers = None
  else:  
    registers = api.get_register_list(group)
    if not registers:
      return
    
  print( "Reading..." )
  data = api.read_modbus_data( registers=registers )
  if data: 
    for register, item in data.items():
      print("- {}: {:50s} {} {}".format( register, item["name"], item["value"], item["unit"]))

#-------------------------------
def write_register(api):
  print( "-------------------------------------" )
  print( "Current settings of writable registers:" )
  print( "Reg   Name                           Value  Unit" )
  print( "----- ------------------------------ ------ ----" )
  register_map_sorted = dict(sorted(register_map.items()))
  for register, item in register_map_sorted.items():
    if item["writable"]: 
      data = api.read_modbus_data( registers=[register] )
      value = ""
      if data: 
        value = data[register]["value"]
      unit = item["unit"] if item["unit"] else ""
      print("{:5s} {:30s} {:6s} {:4s} ".format(register, item["name"], str(value), unit ))

  print( "" )
  register = input("Register: ")
  value = input("Value: ")

  print( "WARNING: Be careful when writing registers to your Inverter!" )
  yn = input("Do you really want to set register {} to '{}'? (y/N)".format(register,value))
  if yn == "y" or yn == "Y": 
    ret = api.write_register( register=register, value=value)
    if ret == True:
      print("New value successfully set")  
    else:
      print("Writing failed")  
  else:
    print("Write aborted by user")  

#-------------------------------
def list_register_config(api):
  print( "-------------------------------------" )
  print( "Reg   MQTT Parameter                 Unit Mode Group           Name                   " )
  print( "----- ------------------------------ ---- ---- --------------- -----------------------" )
  register_map_sorted = dict(sorted(register_map.items()))
  for register, item in register_map_sorted.items():
    if not register.isnumeric(): # non-numeric registers are deemed to be calculated pseudo-registers
      register = "" 
    mqtt = item["mqtt"] if item["mqtt"] else ""
    unit = item["unit"] if item["unit"] else ""
    group = item["group"] if item["group"] else ""
    mode = "RW" if item["writable"] else "R"
    print("{:5s} {:30s} {:4s} {:4s} {:15s} {}".format(register, mqtt, unit, mode, group, item["name"]))
 
#-------------------------------
def list_register_config_by_groups(api):
  for group in register_groups:  
    print( "-------------------------------------" )
    print( "Group {}:".format(group) ) 
    print( "" )
    print( "Reg   MQTT Parameter                 Unit Mode Name                   " )
    print( "----- ------------------------------ ---- ---- -----------------------" )
    register_map_sorted = dict(sorted(register_map.items()))
    for register, item in register_map_sorted.items():
      if item["group"]==group: 
        if not register.isnumeric(): # non-nu1meric registers are deemed to be calculated pseudo-registers
          register = "" 
        mqtt = item["mqtt"] if item["mqtt"] else ""
        unit = item["unit"] if item["unit"] else ""
        mode = "RW" if item["writable"] else "R"
        print("{:5s} {:30s} {:4s} {:4s} {}".format(register, mqtt, unit, mode, item["name"]))
    print( "" )

#-------------------------------
def main(): 
  api = MTECmodbusAPI.MTECmodbusAPI()
  api.connect( ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'] )

  while True:
    print( "=====================================" )
    print( "Menu:")
    print( "  1: List all known registers" )
    print( "  2: List register configuration by groups" )
    print( "  3: Read register group from Inverter" )
    print( "  4: Read single register from Inverter" )
    print( "  5: Write register to Inverter" )
    print( "  x: Exit" )
    opt = input("Please select: ")
    if opt == "1": 
      list_register_config(api)
    elif opt == "2": 
      list_register_config_by_groups(api)
    if opt == "3": 
      read_register_group(api)
    elif opt == "4": 
      read_register(api)
    elif opt == "5": 
      write_register(api)
    elif opt == "x" or opt == "X":  
      break
  
  api.disconnect()
  print( "Bye!")

#-------------------------------
if __name__ == '__main__':
  main()

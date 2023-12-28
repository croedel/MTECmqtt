#!/usr/bin/env python3
"""
This tool enables to write parameters using MTECmodbusapi.
(c) 2023 by Christian Rödel 
"""
import logging
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from config import cfg
import argparse
import MTECmodbusAPI

#-----------------------------
def parse_options():
  parser = argparse.ArgumentParser(description='MTEC Modbus register setting tool. Allows to write Modbus registers of a MTEC inverter.', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument( '-r', '--register', help='Register (id) you want to write to' )
  parser.add_argument( '-v', '--value', help='Value you want to write')
  parser.add_argument( '-y', '--yes', action='store_true', help='Do not ask for confirmation')
  return parser.parse_args()
 
#-------------------------------
def main():
  args = parse_options()
#  if not args.register or not args.data:
#    print("Missing parameter")
#    exit(1)  

#  register = str(args.register)
#  value = str(args.data) 
  register = '30230'
  value = '257' 

  api = MTECmodbusAPI.MTECmodbusAPI()
  api.connect( ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'] )

  data = api.read_modbus_data( registers=[register] )
  if data: 
    item = data.get(register)
    line = "Current value of register {} ({}): {} {}".format( register, item["name"], item["value"], item["unit"] )
    print( line )

  if args.yes:
    yn = "y"
  else:  
    yn = input("Do you want to set it to '{}'? (y/N)".format(value))
  if yn == "y" or yn == "Y": 
    ret = api.write_register( register=register, value=value)
    if ret == True:
      data = api.read_modbus_data( registers=[register] )
      if data: 
        item = data.get(register)
        line = "New value of register {} ({}): {} {}".format( register, item["name"], item["value"], item["unit"] )
        print( line )
    else:
      print("Writing failed")  
  else:
    print("Aborted by user")  
  api.disconnect()

#-------------------------------
if __name__ == '__main__':
  main()

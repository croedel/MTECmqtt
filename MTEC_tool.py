#!/usr/bin/env python3
"""
This tool enables to query MTECmodbusapi and can act as demo on how to use the API
(c) 2023 by Christian Rödel 
"""
from config import cfg
import argparse
import sys
import MTECmodbusAPI

#-----------------------------
def parse_options():
  parser = argparse.ArgumentParser(description='MTEC Modbus data command line tool. Allows to read and export Modbus registers from an MTEC inverter.', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument( '-t', '--type', choices=["all", "essential"], default="all", help='Defines set of registers to export.' )
  parser.add_argument( '-r', '--registers', help='Comma separated list of registers which shall be retrieved' )
  parser.add_argument( '-c', '--csv', action='store_true', help='Export as CSV')
  parser.add_argument( '-f', '--file', help='Write data to <FILE> instead of stdout')
  return parser.parse_args()
 
#-------------------------------
def main():
  args = parse_options()

  # redirect stdout to file (if defined as command line parameter)
  if args.file:  
    try:
      print( "Writing output to '{}' ...".format(args.file) )
      original_stdout = sys.stdout
      sys.stdout = open(args.file, 'w')
    except:  
      print( "ERROR - Unable to create file '{}'".format(args.file) )
      exit(1)

  registers = None
  if args.type == "essential":       
    registers = [ '10105', '11000', '11016', '11018', '11020', '11028', '30258', '33000' ]

  if args.registers:
    registers = []
    reg_str = args.registers.split(",")
    for addr in reg_str:
      registers.append(addr.strip())  

  # Do the export
  data = MTECmodbusAPI.read_modbus_data(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], 
                                        slave=cfg['MODBUS_SLAVE'], registers=registers)

  if data: 
    for register, item in data.items():
      if args.csv:
        line = "{};{};{};{}".format( register, item["name"], item["value"], item["unit"] )
      else:
        line = "- {}: {:50s} {} {}".format( register, item["name"], item["value"], item["unit"] )
      print( line )

  # cleanup
  if args.file:
    sys.stdout.close()  
    sys.stdout = original_stdout
    print( "done" )

#-------------------------------
if __name__ == '__main__':
  main()

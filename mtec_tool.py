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
  parser.add_argument( '-a', '--append', action='store_true', help='Use as modifier in combination with --file argument to append data to file instead of replacing it')
  return parser.parse_args()
 
#-------------------------------
def main():
  args = parse_options()
  print( "Reading data..." )

  # redirect stdout to file (if defined as command line parameter)
  if args.file:  
    try:
      if args.csv:  
        print( "Writing output as CSV to '{}'".format(args.file) )
      else:
        print( "Writing output to '{}'".format(args.file) )
      if args.append:
        f_mode = 'a'
      else:
        f_mode = 'w'             
      original_stdout = sys.stdout
      sys.stdout = open(args.file, f_mode)
    except:  
      print( "ERROR - Unable to create file '{}'".format(args.file) )
      exit(1)

  registers = None
  if args.type == "essential":       
    registers = [ '10100', '10105', '11028', '11000', '30258', '11016', '30230', '33000', 
               '31000', '31001', '31003', '31004', '31005', '31102', '31104', '31108', '31110', '31112' ]

  if args.registers:
    registers = []
    reg_str = args.registers.split(",")
    for addr in reg_str:
      registers.append(addr.strip())  

  # Do the export
  api = MTECmodbusAPI.MTECmodbusAPI()
  api.connect( ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'] )
  data = api.read_modbus_data( registers=registers )
  api.disconnect()

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
  print( "Data completed" )

#-------------------------------
if __name__ == '__main__':
  main()

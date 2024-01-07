#!/usr/bin/env python3
"""
This tool enables to query MTECmodbusapi and export the data in various ways.
(c) 2024 by Christian Rödel 
"""
from config import cfg, register_groups
import argparse
import sys
import MTECmodbusAPI

#-----------------------------
def parse_options():
  groups = sorted(register_groups)
  groups.append("all")

  parser = argparse.ArgumentParser(description='MTEC Modbus data export tool. Allows to read and export Modbus registers from an MTEC inverter.', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument( '-g', '--group', choices=groups, default="all", help='Group of registers you want to export' )
  parser.add_argument( '-r', '--registers', help='Comma separated list of registers which shall be retrieved' )
  parser.add_argument( '-c', '--csv', action='store_true', help='Export as CSV')
  parser.add_argument( '-f', '--file', help='Write data to <FILE> instead of stdout')
  parser.add_argument( '-a', '--append', action='store_true', help='Use as modifier in combination with --file argument to append data to file instead of replacing it')
  return parser.parse_args()
 
#-------------------------------
def main():
  args = parse_options()
  api = MTECmodbusAPI.MTECmodbusAPI()
  print( "Reading data..." )

  # redirect stdout to file (if defined as command line parameter)
  if args.file:  
    try:
      print( "Writing output to '{}'".format(args.file) )
      if args.csv:  
        print( "CSV format selected" )
      if args.append:
        print( "Append mode selected" )
        f_mode = 'a'
      else:
        f_mode = 'w'             
      original_stdout = sys.stdout
      sys.stdout = open(args.file, f_mode)
    except:  
      print( "ERROR - Unable to open output file '{}'".format(args.file) )
      exit(1)

  registers = None
  if args.group and args.group != "all":
    registers = sorted(api.get_register_list(args.group))

  if args.registers:
    registers = []
    reg_str = args.registers.split(",")
    for addr in reg_str:
      registers.append(addr.strip())  

  # Do the export
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

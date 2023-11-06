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
  parser = argparse.ArgumentParser(description='MTEC data command line tool. Exports data from a MTEC device.', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument( '-t', '--type', choices=["full", "essential"], default="full", help='Defines which parameters to export' )
  parser.add_argument( '-a', '--addresses', help='Custom list of addresses to export' )
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

  addresses = None
  if args.type == "essential":       
    addresses = [ '10105', '11000', '11016', '11018', '11020', '11028', '30258', '33000' ]

  if args.addresses:
    addresses = []
    addr_str = args.addresses.split(",")
    for addr in addr_str:
      addresses.append(addr.strip())  

  # Do the export
  data = MTECmodbusAPI.read_modbus_data(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], 
                                        slave=cfg['MODBUS_SLAVE'], addresses=addresses)

  if data: 
    for address, item in data.items():
      if args.csv:
        line = "{};{};{};{}".format( address, item["name"], item["value"], item["unit"] )
      else:
        line = "- {}: {:50s} {} {}".format( address, item["name"], item["value"], item["unit"] )
      print( line )

  # cleanup
  if args.file:
    sys.stdout.close()  
    sys.stdout = original_stdout
    print( "done" )

#-------------------------------
if __name__ == '__main__':
  main()

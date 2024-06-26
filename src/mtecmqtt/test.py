#!/usr/bin/env python3
"""
Test connection to M-TEC Energybutler
(c) 2024 by Christian Rödel 
"""
from pymodbus.client import ModbusTcpClient
from pymodbus.framer import Framer
import logging

#=====================================================
class MTECmodbusAPI:
  #-------------------------------------------------
  def __init__( self ):
    self.modbus_client = None
    self.slave = 0
    self._cluster_cache = {}
    logging.debug("API initialized")

  def __del__(self):
    self.disconnect()

  #-------------------------------------------------
  # Connect to Modbus server
  def connect( self, ip_addr, port, slave ):
    self.slave = slave
    
    framer = "rtu"
    logging.debug("Connecting to server {}:{} (framer={})".format(ip_addr, port, framer))
    self.modbus_client = ModbusTcpClient(ip_addr, port, framer=Framer(framer), timeout=5, retries=3, retry_on_empty=True )

    if self.modbus_client.connect():
      logging.debug("Successfully connected to server {}:{}".format(ip_addr, port))
      return True
    else:
      logging.error("Couldn't connect to server {}:{}".format(ip_addr, port))
      return False

  #-------------------------------------------------
  # Disconnect from Modbus server
  def disconnect( self ):
    if self.modbus_client and self.modbus_client.is_socket_open():
      self.modbus_client.close()
      logging.debug("Successfully disconnected from server")


#--------------------------------
# The main() function is just a demo code how to use the API
def main():
  logging.basicConfig()
  logging.getLogger().setLevel(logging.DEBUG)

  print( "Please enter" )
  ip_addr = input("espressif server IP Adress: ")
  port = input("espressif Port (Standard is 5743): ")

  api = MTECmodbusAPI()
  api.connect(ip_addr=ip_addr, port=port, slave=252)
  api.disconnect()

#--------------------------------------------      
if __name__ == '__main__':
  main()

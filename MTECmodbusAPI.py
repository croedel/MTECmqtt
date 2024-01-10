#!/usr/bin/env python3
"""
Modbus API for M-TEC Energybutler
(c) 2023 by Christian Rödel 
"""
from config import cfg, register_map
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.framer import Framer
import logging

#=====================================================
class MTECmodbusAPI:
  #-------------------------------------------------
  def __init__( self ):
    self.modbus_client = None
    self.slave = 0
    logging.debug("API initialized")

  def __del__(self):
    self.disconnect()

  #-------------------------------------------------
  # Connect to Modbus server
  def connect( self, ip_addr, port, slave ):
    self.slave = slave
    
    framer = cfg.get("MODBUS_FRAMER", "rtu")
    logging.debug("Connecting to server {}:{} (framer={})".format(ip_addr, port, framer))
    self.modbus_client = ModbusTcpClient(ip_addr, port, framer=Framer(framer), timeout=cfg["MODBUS_TIMEOUT"],
                                         retries=cfg["MODBUS_RETRIES"], retry_on_empty=True )

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
  # This is the main API function. It either fetches all registers or a list of given registers
  def read_modbus_data(self, registers=None):
    data = {}
    logging.debug("Retrieving data...")

    if registers == None: # Create liset of all (numeric) registers
      registers = []
      for register in register_map:
        if register.isnumeric(): # non-numeric registers are deemed to be calculated pseudo-registers
          registers.append(register)

    cluster_list = self._get_register_clusters(registers)
    for reg_cluster in cluster_list:
      offset = 0
      logging.info("Fetching data for cluster start: {}, length {}".format(reg_cluster["start"], reg_cluster["length"]))
      rawdata = self._read_registers(reg_cluster["start"], reg_cluster["length"])
      if rawdata:
        for item in reg_cluster["items"]:
          data_decoded = self._decode_rawdata(rawdata, offset, item)
          if data_decoded:
            register = str(reg_cluster["start"] + offset)
            data.update( {register: data_decoded} )
          else:
            logging.error("Decoding error while decoding register {}".format(register))
          offset += item["length"]

    logging.debug("Data retrieval completed")
    return data

  #--------------------------------
  def write_register(self, register, value):
    # Lookup register
    item = register_map.get(str(register), None)
    if not item:
      logging.error("Can't write unknown register: {}".format(register))
      return False
    elif item.get("writable", False) == False:
      logging.error("Can't write register which is marked read-only: {}".format(register))
      return False

    # check value
    try:
      if isinstance(value, str):
        if "." in value:
          value = float(value)
        else:
          value = int(value)  
    except Exception as ex:
      logging.error("Invalid numeric value: {}".format(value))
      return False

    # adjust scale 
    if item["scale"] > 1:
        value *= item["scale"]

    try:
      result = self.modbus_client.write_register(address=int(register), value=int(value), slave=self.slave )
    except Exception as ex:
      logging.error("Exception while writing register {} to pymodbus: {}".format(register, ex))
      return False

    if result.isError():
      logging.error("Error while writing register {} to pymodbus".format(register))
      return False
    return True

  #--------------------------------
  # Helper to get a list of all registers which belong to a given group
  def get_register_list( self, group ):
    registers = []
    for register, item in register_map.items():
      if item["group"] == group:
        registers.append(register)

    if len(registers)==0:
      logging.error("Unknown or empty register group: {}".format(group))
      return None              
    return registers

  #--------------------------------
  # Cluster registers in order to optimize modbus traffic    
  def _get_register_clusters( self, registers ):
    registers.sort()
    cluster = { 
      "start": 0,     
      "length": 0,
      "items": []   
    }
    cluster_list = []
    
    for register in registers:
      if register.isnumeric(): # ignore non-numeric pseudo registers
        item = register_map.get(register)
        if item:
          if int(register) != cluster["start"] + cluster["length"]: 
            if cluster["start"] > 0: # except for first cluster 
              cluster_list.append(cluster)
            cluster = { 
              "start": int(register),     
              "length": 0,
              "items": []   
            }
          cluster["length"] += item["length"]  
          cluster["items"].append(item)
        else:
          logging.warning("Unknown register: {} - skipped.".format(register))

    if cluster["start"] > 0: # append last cluster
      cluster_list.append(cluster)

    return cluster_list
  
  #--------------------------------
  def _read_registers(self, register, length):
    try:
      result = self.modbus_client.read_holding_registers(address=int(register), count=length, slave=self.slave)
    except Exception as ex:
      logging.error("Exception while reading register {} from pymodbus: {}".format(register, ex))
      return None
    if result.isError():
      logging.error("Error while reading register {} from pymodbus".format(register))
      return None
    return result

  #--------------------------------
  def _decode_rawdata(self, rawdata, offset, item):
    data = {}   
    val = None
    start = rawdata.registers[offset:]
    decoder = BinaryPayloadDecoder.fromRegisters(registers=start, byteorder=Endian.BIG, wordorder=Endian.BIG)
    item["type"] = item["type"]
    if item["type"] == 'U16':
      val = decoder.decode_16bit_uint()
    elif item["type"] == 'I16':
      val = decoder.decode_16bit_int()
    elif item["type"] == 'U32':
      val = decoder.decode_32bit_uint()
    elif item["type"] == 'I32':
      val = decoder.decode_32bit_int()
    elif item["type"] == 'BYTE':
      if item["length"] == 1:
        val = "{:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
      elif item["length"] == 2:
        val = "{:02d} {:02d}  {:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                  decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
      elif item["length"] == 4:
        val = "{:02d} {:02d} {:02d} {:02d}  {:02d} {:02d} {:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                  decoder.decode_8bit_uint(), decoder.decode_8bit_uint(),
                                                  decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                  decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
    elif item["type"] == 'BIT':
      if item["length"] == 1:
        val = "{:08b}".format( decoder.decode_8bit_uint() )
      if item["length"] == 2:
        val = "{:08b} {:08b}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
    elif item["type"] == 'DAT':
      val = "{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), decoder.decode_8bit_uint(),
                      decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
    elif item["type"] == 'STR':
      val = decoder.decode_string(item["length"]*2).decode()
    else:
      logging.error("Unknown type {} to decode".format(item["type"]))
      return data
    
    if val and item["scale"] > 1:
      val /= item["scale"]
    data = { "name":item["name"], "value":val, "unit":item["unit"] } 
    return data

#--------------------------------
# The main() function is just a demo code how to use the API
def main():
  logging.basicConfig()
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)

  api = MTECmodbusAPI()
  api.connect(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'])

  # fetch all available data
  logging.info("Fetching all data")
  data = api.read_modbus_data()
  for param, val in data.items():
    logging.info("- {} : {}".format(param, val))

  api.disconnect()

#--------------------------------------------      
if __name__ == '__main__':
  main()

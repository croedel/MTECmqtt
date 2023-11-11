#!/usr/bin/env python3
"""
Modbus API for M-TEC Energybutler
(c) 2023 by Christian Rödel 
"""
from config import cfg
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import ModbusException
import logging

#--------------------------------
# These are the modbus registers and how to interpret them
# Data thankfully taken from https://smarthome.exposed/wattsonic-hybrid-inverter-gen3-modbus-rtu-protocol/
register_map = {
# Register   Name                                      Length, Type,  Unit,   Scale
	'10000': [ 'Inverter serial number',                      8, 'STR',	'',     None  ],		
	'10008': [ 'Equipment Info',                              1, 'BYTE', '',    None  ],	
  '10011': [ 'Firmware Version ',	                          4, 'BYTE', '',	  None  ],
	'10100': [ 'Inverter date',                               3, 'DAT',	'',     None  ],		
	'10105': [ 'Inverter Running Status',                     1, 'U16', '',   	None  ],
  '10112': [ 'Fault Flag1',                                 2, 'BIT', '',	    None	], 
  '10114': [ 'Fault Flag2',                                 2, 'BIT', '',	    None	], 
  '10120': [ 'Fault Flag3',                                 2, 'BIT', '',	    None	], 
  '10994': [ 'Phase A Power on Meter',	                    2, 'I32', 'kW',	  1000	],
  '10996': [ 'Phase B Power on Meter',	                    2, 'I32', 'kW',	  1000	],
  '10998': [ 'Phase C Power on Meter',	                    2, 'I32', 'kW',	  1000	],
  '11000': [ 'Total Power on Meter',	                      2, 'I32', 'kW',	  1000	],
  '11002': [ 'Total Grid-Injection Energy on Meter',	      2, 'U32', 'kWh',  100	  ],
  '11004': [ 'Total Purchasing Energy from Grid on Meter',	2, 'U32', 'kWh',  100	  ],
  '11006': [ 'Grid Lines A/B Voltage',	                    1, 'U16', 'V',	  10	  ],
  '11007': [ 'Grid Lines B/C Voltage',	                    1, 'U16', 'V',	  10	  ],
  '11008': [ 'Grid Lines C/A Voltage',	                    1, 'U16', 'V',	  10	  ],
  '11009': [ 'Grid Phase A Voltage',	                      1, 'U16', 'V',	  10	  ],
  '11010': [ 'Grid Phase A Current',	                      1, 'U16', 'A',	  10	  ],
  '11011': [ 'Grid Phase B Voltage',	                      1, 'U16', 'V',	  10	  ],
  '11012': [ 'Grid Phase B Current',	                      1, 'U16', 'A',	  10	  ],
  '11013': [ 'Grid Phase C Voltage',	                      1, 'U16', 'V',	  10	  ],
  '11014': [ 'Grid Phase C Current',	                      1, 'U16', 'A',	  10	  ],
  '11015': [ 'Grid Frequency',	                            1, 'U16', 'Hz',	  100	  ],
  '11016': [ 'P_AC',	                                      2, 'I32', 'kW',	  1000	],
  '11018': [ 'Total PV Generation on that day',	            2, 'U32', 'kWh',  10	  ],
  '11020': [ 'Total PV Generation from Installation',       2, 'U32', 'kWh',  10	  ],
  '11022': [ 'Total PV Generation Time from Installation',	2, 'U32', 'h',	  None  ],
  '11028': [ 'PV Input Total Power',	                      2, 'U32', 'kW',	  1000	],
  '11032': [ 'Temperature Sensor 1',	                      1, 'I16', '℃',	 10	   ],
  '11033': [ 'Temperature Sensor 2',	                      1, 'I16', '℃',	 10	   ],
  '11034': [ 'Temperature Sensor 3',	                      1, 'I16', '℃',	 10	   ],
  '11035': [ 'Temperature Sensor 4',	                      1, 'I16', '℃',	 10	   ],
  '11038': [ 'PV1 Voltage',	                                1, 'U16', 'V',	  10	  ],
  '11039': [ 'PV1 Current',	                                1, 'U16', 'A',	  10	  ],
  '11040': [ 'PV2 Voltage',	                                1, 'U16', 'V',	  10	  ],
  '11041': [ 'PV2 Current',	                                1, 'U16', 'A',	  10	  ],
  '11062': [ 'PV1 Input Power',                             2, 'U32', 'kW',	  1000	],
  '11064': [ 'PV2 Input Power',                             2, 'U32', 'kW',	  1000	],
  '30200': [ 'Backup_A_V',	                                1, 'U16', 'V',	  10	  ],
  '30201': [ 'Backup_A_I',	                                1, 'U16', 'A',	  10	  ],
  '30202': [ 'Backup_A_F',	                                1, 'U16', 'Hz',	  100	  ],
  '30204': [ 'Backup_A_P',	                                2, 'I32', 'kW',	  1000  ],
  '30210': [ 'Backup_B_V',	                                1, 'U16', 'V',	  10	  ],
  '30211': [ 'Backup_B_I',	                                1, 'U16', 'A',	  10	  ],
  '30212': [ 'Backup_B_F',	                                1, 'U16', 'Hz',	  100	  ],
  '30214': [ 'Backup_B_P',	                                2, 'I32', 'kW',	  1000  ],
  '30220': [ 'Backup_C_V',	                                1, 'U16', 'V',	  10	  ],
  '30221': [ 'Backup_C_I',	                                1, 'U16', 'A',	  10	  ],
  '30222': [ 'Backup_C_F',	                                1, 'U16', 'Hz',	  100	  ],
  '30224': [ 'Backup_C_P',	                                2, 'I32', 'kW',	  1000  ],
  '30230': [ 'Total_Backup_P',	                            2, 'I32', 'kW',	  1000  ],
  '30236': [ 'Invt_A_P',	                                  2, 'I32', 'kW',	  1000  ],
  '30242': [ 'Invt_B_P',	                                  2, 'I32', 'kW',	  1000  ],
  '30248': [ 'Invt_C_P',	                                  2, 'I32', 'kW',	  1000  ],
  '30254': [ 'Battery_V',	                                  1, 'U16', 'V',	  10	  ],
  '30255': [ 'Battery_I',	                                  1, 'I16', 'A',	  10	  ],
  '30256': [ 'Battery_Mode',	                              1, 'U16', '',	    None  ],
  '30258': [ 'Battery_P',                                   2, 'I32', 'kW',	  1000  ],
  '31000': [ 'Grid Injection Energy on that day[Meter]',	  1, 'U16', 'kWh',  10	  ],
  '31001': [ 'Grid Purchasing Energy on that day[Meter]',   1, 'U16', 'kWh',  10	  ],
  '31002': [ 'Backup Output Energy on that day',	          1, 'U16', 'kWh',  10	  ],
  '31003': [ 'Battery Charge Energy on that day',           1, 'U16', 'kWh',  10	  ],
  '31004': [ 'Battery Discharge Energy on that day',	      1, 'U16', 'kWh',  10	  ],
  '31005': [ 'PV Generation Energy on that day',	          1, 'U16', 'kWh',  10	  ],
  '31006': [ 'Loading Energy on that day',	                1, 'U16', 'kWh',  10	  ],
  '31008': [ 'Energy Purchased from Grid on that day',	    1, 'U16', 'kWh',  10	  ],
  '31102': [ 'Total Energy injected to grid',               2, 'U32', 'kWh',  10	  ],
  '31104': [ 'Total Energy Purchased from Grid from Meter', 2, 'U32', 'kWh',  10	  ],
  '31106': [ 'Total Output Energy on backup port',	        2, 'U32', 'kWh',  10	  ],
  '31108': [ 'Total Energy Charged to Battery',             2, 'U32', 'kWh',  10	  ],
  '31110': [ 'Total Energy Discharged from Battery',	      2, 'U32', 'kWh',  10	  ],
  '31112': [ 'Total PV Generation',                         2, 'U32', 'kWh',  10	  ],
  '31114': [ 'Total Loading Energy consumed at grid side',	2, 'U32', 'kWh',  10	  ],
  '31118': [ 'Total Energy Purchased from Grid',            2, 'U32', 'kWh',  10	  ],
  '33000': [ 'SOC',	                                        1, 'U16', '%',	  100	  ],
  '33001': [ 'SOH',	                                        1, 'U16', '%',	  100	  ],
  '33002': [ 'BMS Status',	                                1, 'U16', '',	    None  ],
  '33003': [ 'BMS Pack Temperature',	                      1, 'U16', '℃',	 10	   ],
  '33009': [ 'Max Cell Temperature',	                      1, 'U16', '℃',	 10	   ],
  '33011': [ 'Min Cell Temperature',	                      1, 'U16', '℃',	 10	   ],
  '33013': [ 'Max Cell Voltage',	                          1, 'U16', 'V',	  1000	],
  '33015': [ 'Min Cell Voltage',	                          1, 'U16', 'V',	  1000	],
}
 
#--------------------------------
# This is the main API function
# It either fetches all registers or a list of given registers
def read_modbus_data(ip_addr, port, slave, registers=None):
  data = {}
  # Connect to Modbus server
  logging.info("Connecting to server {}:{}".format(ip_addr, port))
  client = ModbusTcpClient(ip_addr, port, framer=ModbusRtuFramer, timeout=cfg["MODBUS_TIMEOUT"])

  if client.connect():
    logging.info("Retrieving data...")
    if registers == None: # fetch all registers
      for register, item in register_map.items():
        reg_data = read_register(client, register=register, slave=slave, item=item) 
        if reg_data:
          data.update( reg_data )
    else: # fetch list of given registers
      for register in registers:
        item = register_map.get(register)
        if item:
          reg_data = read_register(client, register=register, slave=slave, item=item) 
          if reg_data:
            data.update( reg_data )
        else:
          logging.warning("Unknowd register: {} - skipped.".format(register))
  
    logging.info("Data retrieval completed")
    client.close()
  else:
    logging.error("Couldn't connect to server {}:{}".format(ip_addr, port))

  return data
  
#--------------------------------
def read_register(client, register, slave, item):
  data = {}
  try:
    result = client.read_holding_registers(address=int(register), count=item[1], slave=slave)
  except Exception as ex:
    logging.error("Exception while reading register {} from pymodbus: {}".format(register, ex))
    return data

  if result.isError():
    logging.error("Error while reading register {} from pymodbus".format(register))
    return data
  
  val = None
  decoder = BinaryPayloadDecoder.fromRegisters(result.registers,byteorder=Endian.BIG, wordorder=Endian.BIG)
  if item[2] == 'U16':
    val = decoder.decode_16bit_uint()
  elif item[2] == 'I16':
    val = decoder.decode_16bit_int()
  elif item[2] == 'U32':
    val = decoder.decode_32bit_uint()
  elif item[2] == 'I32':
    val = decoder.decode_32bit_int()
  elif item[2] == 'BYTE':
    if item[1] == 1:
      val = "{:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
    elif item[1] == 2:
      val = "{:02d} {:02d}  {:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                 decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
    elif item[1] == 4:
      val = "{:02d} {:02d} {:02d} {:02d}  {:02d} {:02d} {:02d} {:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                 decoder.decode_8bit_uint(), decoder.decode_8bit_uint(),
                                                 decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), 
                                                 decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
  elif item[2] == 'BIT':
    if item[1] == 1:
      val = "{:08b}".format( decoder.decode_8bit_uint() )
    if item[1] == 2:
      val = "{:08b} {:08b}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
  elif item[2] == 'DAT':
    val = "{:02d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format( decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), decoder.decode_8bit_uint(),
                    decoder.decode_8bit_uint(), decoder.decode_8bit_uint(), decoder.decode_8bit_uint() )
  elif item[2] == 'STR':
    val = decoder.decode_string(item[1]*2).decode()
  else:
    logging.error("Unknown type {} to decode register {}".format(item[2], register))
    return data
  
  if val and item[4] and item[4]>0:
    val /= item[4]
  data[register] = { "name":item[0], "value":val, "unit":item[3] } 

  return data
  
#--------------------------------
# The main() function is just a demo code how to use the API
def main():
  logging.basicConfig()
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)

  # fetch all available data
  logging.info("Fetching all data")
  data = read_modbus_data(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'])
  for param, val in data.items():
    logging.info("- {} : {}".format(param, val))

  # fetch selected  registers
  logging.info("Fetching selected data")
  registers = [ '11000', '11016', '11018', '11020', '11028', '30258', '33000', '10000', '10100' ]
  data = read_modbus_data(ip_addr=cfg['MODBUS_IP'], port=cfg['MODBUS_PORT'], slave=cfg['MODBUS_SLAVE'],  registers= registers)
  for param, val in data.items():
    logging.info("- {} : {}".format(param, val))


#--------------------------------------------      
if __name__ == '__main__':
  main()

""" 
Read YAML config files
(c) 2024 by Christian Rödel 
"""
import yaml
import os
import sys
import logging

#----------------------------------------
# Read configuration from YAML file
def init_config():
  # Look in different locations for config.yaml file
  conf_files = []
  cfg_path = os.environ.get('XDG_CONFIG_HOME') or os.environ.get('APPDATA')
  if cfg_path: # Usually something like ~/.config/mtecmqtt/config.yaml resp. 'C:\\Users\\xxxx\\AppData\\Roaming'
    conf_files.append(os.path.join(cfg_path, "mtecmqtt", "config.yaml"))  
  else:
    conf_files.append(os.path.join(os.path.expanduser("~"), ".config", "mtecmqtt", "config.yaml"))  # ~/.config/mtecmqtt/config.yaml
  conf_files.append(os.path.join(os.path.expanduser("~"), "mtecmqtt", "config.yaml"))  # ~/mtecmqtt/config.yaml
  
  cfg = False
  for fname_conf in conf_files:
    try:
      with open(fname_conf, 'r', encoding='utf-8') as f_conf:
        cfg = yaml.safe_load(f_conf)
        logging.info("Using config YAML file: {}".format(fname_conf) )      
        break
    except IOError as err:
      logging.debug("Couldn't open config YAML file: {}".format(str(err)) )
    except yaml.YAMLError as err:
      logging.debug("Couldn't read config YAML file {}: {}".format(fname_conf, str(err)) )

  return cfg  

#----------------------------------------
# Read inverter registers and their mapping from YAML file
def init_register_map():
  BASE_DIR = os.path.dirname(__file__) # Base installation directory
  try:
    fname_regs = os.path.join(BASE_DIR, "registers.yaml")
    with open(fname_regs, 'r', encoding='utf-8') as f_regs:
      r_map = yaml.safe_load(f_regs)
  except IOError as err:
    logging.fatal("Couldn't open registers YAML file: {}".format(str(err)))
    sys.exit(1)
  except yaml.YAMLError as err:
    logging.fatal("Couldn't read config YAML file {}: {}".format(fname_regs, str(err)) )
    sys.exit(1)
    
  # Syntax checks 
  register_map = {}
  p_mandatory = [
    "name", 
  ]
  p_optional = [ 
    # param, default
    [ "length", None ], 
    [ "type", None ],
    [ "unit", "" ],
    [ "scale", 1 ],
    [ "writable", False ],
    [ "mqtt", None ],
    [ "group", None ],
  ] 
  register_groups = []

  for key, val in r_map.items():
    # Check for mandatory paramaters
    for p in p_mandatory: 
      error = False
      if not val.get(p):
        logging.warning("Skipping invalid register config: {}. Missing mandatory parameter: {}.".format( key, p ))
        error = True
        break

    if not error: # All madatory parameters found   
      item = val.copy()  
      # Check optional parameters and add defaults, if not found
      for p in p_optional:  
        if not item.get(p[0]):
          item[p[0]] = p[1]
      register_map[key] = item # Append to register_map
      if item["group"] and item["group"] not in register_groups:
        register_groups.append(item["group"]) # Append to group list
  return register_map, register_groups

#----------------------------------------
logging.basicConfig( level=logging.INFO, format="[%(levelname)s] %(filename)s: %(message)s" )
cfg = init_config()
if not cfg:
  logging.fatal("Couldn't open config YAML file")
  sys.exit(1)
register_map, register_groups = init_register_map()

#--------------------------------------
# Test code only
if __name__ == "__main__":
  logging.info( "Config: {}".format( str(cfg)) )
  logging.info( "Register_map: {}".format( str(register_map)) )
  
""" Read YAML config files
"""
import yaml
import os
import logging

#----------------------------------------
# Read configuration from YAML file
def init_config():
  cfg = {}
  try:
    fname_conf = os.path.join(BASE_DIR, "config.yaml")
    with open(fname_conf, 'r', encoding='utf-8') as f_conf:
      cfg = yaml.safe_load(f_conf)
  except yaml.YAMLError as err:
    logging.error("Couldn't read config YAML file {}: {}".format(f_conf, str(err)) )
  return cfg  

#----------------------------------------
# Read inverter registers and their mapping from YAML file
def init_register_map():
  try:
    fname_regs = os.path.join(BASE_DIR, "registers.yaml")
    with open(fname_regs, 'r', encoding='utf-8') as f_regs:
      r_map = yaml.safe_load(f_regs)
  except yaml.YAMLError as err:
    logging.error("Couldn't read registers YAML file {}: {}".format(f_regs, str(err)) )

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
    [ "writeable", False ],
    [ "mqtt", None ],
    [ "group", None ],
    [ "hass_device_class", None ],
    [ "hass_value_template", "{{ value }}" ],
    [ "hass_state_class", "measurement" ],
  ] 

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
  return register_map

#----------------------------------------
logging.basicConfig( level=logging.INFO, format="[%(levelname)s] %(filename)s: %(message)s" )
BASE_DIR = os.path.dirname(__file__) # Base installation directory
cfg = init_config()
register_map = init_register_map()

#--------------------------------------
# Test code only
if __name__ == "__main__":
  logging.info( "Config: {}".format( str(cfg)) )
  logging.info( "Register_map: {}".format( str(register_map)) )
  
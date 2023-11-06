""" Read YAML config files
"""
import yaml
import os
import logging
import types 

#----------------------------------------
logging.basicConfig( level=logging.INFO, format="[%(levelname)s] %(filename)s: %(message)s" )
BASE_DIR = os.path.dirname(__file__) # Base installation directory

try:
  fname = os.path.join(BASE_DIR, "config.yaml")
  with open(fname, 'r', encoding='utf-8') as myfile:
    cfg = yaml.safe_load(myfile)
except yaml.YAMLError as err:
  logging.error("Couldn't read config file {}: {}".format(fname, str(err)) )

#--------------------------------------
if __name__ == "__main__":
  logging.info( "Config: {}".format( str(cfg)) )
  
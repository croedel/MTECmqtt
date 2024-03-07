import os
import socket
from setuptools import setup, find_packages

#-----------------------
def createConfig():
  print("Creating config.yaml")
  try:
    ip_addr=socket.gethostbyname('espressif')
    print("Found espressif server: {}".format(ip_addr))
  except socket.error:
    print("Couldn't find espressif server")
    ip_addr=input("Please enter IP address of espressif server: ")

  opt=input("Enable HomeAssistant support? (y/N): ")
  if opt.lower()=='y':
    hass_cfg="HASS_ENABLE : True"
  else:    
    hass_cfg="HASS_ENABLE : False"

  try:
    with open("templates/config.yaml", "r") as file: 
      data = file.read()   
      data = data.replace('HASS_ENABLE : False', hass_cfg) 
      data = data.replace('MODBUS_IP : espressif', 'MODBUS_IP : "' + ip_addr +'"') 
  except Exception as ex:
    print("ERROR - Couldn't read 'templates/config.yaml'")
    return False

  try:
    with open("../config.yaml", "w") as file: 
      file.write(data) 
  except Exception as ex:
    print("ERROR - Couldn't write '../config.yaml'")
    return False

  print("Successfully created '../config.yaml'")
  return True

#--------------------------

print("Configuration of MTECmqtt started")

setup(
    name = "MTECmqtt",
    version = "1.0",
    author = "Christian Rödel",
    install_requires = ["pyyaml", "PyModbus", "paho-mqtt" ],
    packages = find_packages(where="src"),
    package_dir = {"": "src"},
    package_data = {"": ["*.yaml"]},
    scripts = ["src/mtec_export.py", "src/mtec_mqtt.py", "src/mtec_util.py", "src/install_systemd_service.sh"]
)

# Check for config.yaml
if os.path.isfile("../config.yaml"):
  print("config.yaml already existing")
else:  
  createConfig()
  
print("Configuration completed")

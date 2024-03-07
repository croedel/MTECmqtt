#!/bin/sh

BASE_DIR=`readlink -f ..`
SVC_TXT="
[Unit]
Description=M-TEC MQTT service 
After=multi-user.target

[Service]
Type=simple
User=USER
WorkingDirectory=BASE_DIR
ExecStart=BASE_DIR/venv/bin/python3 mtec_mqtt.py
Restart=always

[Install]
WantedBy=multi-user.target
"

echo "Installing systemd service"

if [ $(id -u) != "0" ]; then
  echo "This script required root rights. Please restart using 'sudo'"
else
  echo "$SVC_TXT" | sed "s!BASE_DIR!$BASE_DIR!g" | sed "s/USER/$USER/g" > /tmp/mtec_mqtt.service 
  chmod 666 /tmp/mtec_mqtt.service
#  mv /tmp/mtec_mqtt.service /etc/systemd/system
#  systemctl daemon-reload
#  systemctl enable mtec_mqtt.service
#  systemctl start mtec_mqtt.service
  echo "==> systemd service 'mtec_mqtt.service' installed"
fi


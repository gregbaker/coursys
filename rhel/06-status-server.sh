#!/bin/sh

set -e
source ./config.sh

sudo yum install -y python3-pip python3-virtualenv
[ -d /status_server ] || sudo virtualenv /status_server
[ -f /status_server/bin/flask ] || sudo /status_server/bin/python -m pip install flask


cat <<EOF > /etc/systemd/system/status_server.service
# based on https://blog.miguelgrinberg.com/post/running-a-flask-application-as-a-service-with-systemd

[Unit]
Description=docker status monitor service
After=network.target

[Service]
User=coursys
WorkingDirectory=/coursys
ExecStart=/status_server/bin/python -m flask --app docker.status_server run -h 0.0.0.0 -p 8888
Restart=always

[Install]
WantedBy=multi-user.target
EOF


sudo systemctl daemon-reload
sudo systemctl enable status_server
sudo systemctl start status_server
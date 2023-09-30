# must be run as root
# assumes repository root folder is /home/pi/cricket-environmental-control

git config --global --add safe.directory /home/pi/cricket-environmental-control

if ! ls /etc/systemd/system | grep -wqi "cricket-environmental-control"; then

touch /etc/systemd/system/cricket-environmental-control.service
cat << EOF >> /etc/systemd/system/cricket-environmental-control.service
[Unit]
Description=Cricket Environmental Control App
Wants=network-online.target
After=network.target network-online.target

[Service]
ExecStart=bash -c '/home/pi/cricket-environmental-control/run.sh'
User=pi

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cricket-environmental-control.service
systemctl start cricket-environmental-control.service

fi

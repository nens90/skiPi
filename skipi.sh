sudo rm /var/skipi.pid
sudo rm /var/led.mode
ipaddr=$(echo `ifconfig wlan0 2>/dev/null|awk '/inet / {print $2}'`)
echo Got: $ipaddr
sudo python skipi_led.py &
sudo python skipi_receiver.py $ipaddr &
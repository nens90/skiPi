#!/usr/bin/env bash exou

# Install packages
sudo apt-get install -y \
  python3-pip \
  build-essential \
  python-dev \
  git \
  watchdog

# Setup watchdog
echo "bcm2708_wdog" | sudo tee -a /etc/modules
sudo su
cat <<EOT > /etc/watchdog.conf
watchdog-device	= /dev/watchdog
watchdog-timeout = 15
interval = 15
log-dir	= /var/log/watchdog
realtime = yes
priority = 1

EOT
sudo su pi
sudo sed -i 's/run_watchdog=1/run_watchdog=0/g' /etc/default/watchdog
sudo sed -i 's/run_wd_keepalive=1/run_wd_keepalive=0/g' /etc/default/watchdog
sudo update-rc.d -f watchdog remove
sudo update-rc.d -f wd_keepalive remove

# Install neopixel by adafriut
sudo pip3 install RPi.GPIO rpi_ws281x adafruit-circuitpython-neopixel

# Install scroll phat HD
curl -sS https://get.pimoroni.com/scrollphathd | bash

# Install gpio zero for button control
sudo apt install python3-gpiozero

# Blacklist audio module (interferes with PWM and PCM)
echo "blacklist snd_bcm2835" | sudo tee -a /etc/modprobe.d/snd-blacklist.conf

# Install skipi
# Expected location: /home/pi/skipi/skipi.py
sudo su
sudo cat <<EOT >> /etc/init.d/skipi
#!/bin/sh
#/etc/init.d/skipi: start skipi.

### BEGIN INIT INFO
# Provides:          skipi
# Short-Description: Start skipi
# Required-Start:    $local_fs $network $named $remote_fs
# Required-Stop:     $local_fs $remote_fs
# Should-Start:      
# Should-Stop:       
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

# Set handle_watchdog to 1 to start and stop the watchdog.
handle_watchdog=1
# Run command
#ip_addr=$(echo `ifconfig wlan0 2>/dev/null|awk '/inet / {print $2}'`)
#echo Found IP: $ip_addr
cmd_skipi="python -u /home/pi/skipi/skipi.py"
cmd_args="--color white"
log_skipi="/var/log/skipi.log"

echo 1 > /dev/watchdog

case "$1" in
  start)
    if [ $handle_watchdog = 1 ]; then
        /etc/init.d/watchdog stop
    fi
    nohup $cmd_skipi $cmd_args > $log_skipi & 
    ;;

  stop)
    if [ $handle_watchdog = 1 ]; then
        /etc/init.d/watchdog start
    fi
    
    pid_skipi=$(pgrep -f "$cmd_skipi")
    kill -15 $pid_skipi
    ;;
    
  force-stop)
    if [ $handle_watchdog = 1 ]; then
        /etc/init.d/watchdog start
    fi
    
    pid_skipi=$(pgrep -f "$cmd_skipi")
    kill -9 $pid_skipi
    ;;

  restart)
    pid_skipi=$(pgrep -f "$cmd_skipi")
    kill -15 $pid_skipi
    nohup $cmd_skipi $cmd_args > $log_skipi &
    ;;

  *)
    echo "Usage: /etc/init.d/skipi {start|stop|force-stop|restart}"
    exit 1

esac

exit 0

EOT
sudo su pi
sudo chmod +x /etc/init.d/skipi
sudo update-rc.d skipi defaults

# Set execute
(cd /home/pi/skipi && sudo chmod +x skipi.py dbgled.py skibase.py wd.py ws281x.py kfnet.py sphat.py)

# Enable multicast
# Not necessary
#sudo ip route add 224.0.8.0/24 dev wlan0

# ad-hoc


echo "Setup complete!"

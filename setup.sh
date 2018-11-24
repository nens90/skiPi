#!/usr/bin/env bash exou

# Install packages
sudo apt-get install \
  python3-pip \
  build-essential \
  python-dev \
  git \
  scons \
  swig \
  watchdog

# Setup watchdog
echo "bcm2708_wdog" | sudo tee -a /etc/modules
sudo cat <<EOT >> /etc/watchdog.conf
watchdog-device	= /dev/watchdog
watchdog-timeout = 15
interval = 5
log-dir	= /var/log/watchdog
realtime = yes
priority = 1

EOT
sudo sed -i 's/run_watchdog=1/run_watchdog=0/g' /etc/default/watchdog
sudo sed -i 's/run_wd_keepalive=1/run_wd_keepalive=0/g' /etc/default/watchdog
sudo update-rc.d -f watchdog remove
sudo update-rc.d -f wd_keepalive remove

# Install neopixel
cd ~/
git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
scons
cd python
sudo python setup.py install

# Install skipi
cd ~/skipi
sudo cat <<EOT >> /etc/init.d/skipi
#!/bin/sh
#/etc/init.d/skipi: start skipi.

### BEGIN INIT INFO
# Provides:          skipi
# Short-Description: Start skipi
# Required-Start:    $all
# Required-Stop:     $all
# Should-Start:      
# Should-Stop:       
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

# Set handle_watchdog to 1 to start and stop the watchdog.
handle_watchdog=0
# Run command
ip_addr=$(echo `ifconfig wlan0 2>/dev/null|awk '/inet / {print $2}'`)
#echo Found IP: $ip_addr
cmd_skipi="python -u /home/pi/skipi/skipi.py"
log_skipi="/var/log/skipi.log"

echo 1 > /dev/watchdog

case "$1" in
  start)
    if [ $handle_watchdog = 1 ]; then
        /etc/init.d/watchdog stop
    fi
    nohup $cmd_skipi $ip_addr > $log_skipi & 
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
    nohup $cmd_skipi $ip_addr > $log_skipi &
    ;;

  *)
    echo "Usage: /etc/init.d/skipi {start|stop|restart}"
    exit 1

esac

exit 0

EOT
sudo chmod +x /etc/init.d/skipi
sudo update-rc.d skipi defaults

echo "Setup complete!"

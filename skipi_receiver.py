import socket
import os
import time

UDP_IP         = "10.0.0.23"
UDP_PORT       = 5005
MSG_MAX_LEN    = 20
LED_MODE_FILE  = '/var/led.mode'
PID_FILE       = '/var/skipi.pid'

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

time.sleep(0.1) # Wait for skipi.py to create a file with pid.
with open(PID_FILE, 'r') as f:
    skipi_pid =  int(f.read())
    f.close()


while os.path.isfile(PID_FILE):
    data, addr = sock.recvfrom(MSG_MAX_LEN) # buffer size is 20 bytes
    with open(LED_MODE_FILE, 'w') as fd:
        fd.write(data)
        fd.close()
    os.kill(skipi_pid, signal.SIGUSR1)
    print "received message:", data
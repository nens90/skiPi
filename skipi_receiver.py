import socket
import os
import time
import sys # To get ip_address from argv.
import signal

def get_ip_address():
    ip_address = '';
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

UDP_PORT       = 5005
MSG_MAX_LEN    = 20
LED_MODE_FILE  = '/var/led.mode'
PID_FILE       = '/var/skipi.pid'

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
# sock.bind((get_ip_address(), UDP_PORT)) # needs access to google dns
print "\nReceiver - Opening port for ", str(sys.argv[1])
sock.bind((str(sys.argv[1]), UDP_PORT)) # needs access to google dns

time.sleep(10) # Wait for skipi.py to create a file with pid.
with open(PID_FILE, 'r') as f:
    skipi_pid =  int(f.read())
    f.close()
print "Receiver - Have pid: ", str(os.getpid())
print "Receiver - Got pid: ", skipi_pid

while os.path.isfile(PID_FILE):
    data, addr = sock.recvfrom(MSG_MAX_LEN) # buffer size is 20 bytes
    with open(LED_MODE_FILE, 'w',0) as fd:
        fd.write(data)
        fd.write('\n')
        fd.flush()
        fd.close()
    sleep(5)
    os.kill(skipi_pid, signal.SIGUSR1)
    print "Receiver - Got data: ", data
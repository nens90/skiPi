import socket
import time
import signal
import sys

#UDP_IP = '<broadcast>'
UDP_IPS = ["10.0.0.21", "10.0.0.23"]
UDP_PORT = 5005
MSG_MAX_LEN = 20
RAND_MIN = 1
RAND_MAX = 10
LED_INTERVAL = 10 # seconds

def signal_handler(signal, frame):
    message = "0"
    for ip_addr in UDP_IPS: # Send to each IP that we now
        sock.sendto(message, (ip_addr, UDP_PORT))
    sys.exit(0)

print "Sender - UDP target IP:", UDP_IPS
print "Sender - UDP target port:", UDP_PORT

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

led_mode = RAND_MIN
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
#sock.bind(('', 0))
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while True:
    #message = str(random.randint(RAND_MIN, RAND_MAX))
    message = str(led_mode)
    for ip_addr in UDP_IPS: # Send to each IP that we now
        sock.sendto(message, (ip_addr, UDP_PORT))
    print "Sender - Sent: ", message
    time.sleep(LED_INTERVAL)
    led_mode += 1
    if led_mode > RAND_MAX:
        led_mode = RAND_MIN
#end
message = "0"
sock.sendto(message, (ip_addr, UDP_PORT))
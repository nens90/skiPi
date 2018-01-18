import socket
import time

UDP_IP = '<broadcast>'
UDP_PORT = 5005
MSG_MAX_LEN = 20
RAND_MIN = 1
RAND_MAX = 12
LED_INTERVAL = 15 # seconds

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT

led_mode = RAND_MIN
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind(('', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while True:
    #message = str(random.randint(RAND_MIN, RAND_MAX))
    message = str(led_mode)
    sock.sendto(message, (UDP_IP, UDP_PORT))
    print "Sent: ", message
    time.sleep(LED_INTERVAL)
    led_mode += 1
    if led_mode > RAND_MAX:
        led_mode = RAND_MIN
#end
message = "0"
sock.sendto(message, (UDP_IP, UDP_PORT))
import socket

UDP_IP = "10.0.0.255"
UDP_PORT = 5005
MSG_MAX_LEN = 20
RAND_MIN = 1
RAND_MAX = 12

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
while True:
    message = str(random.randint(RAND_MIN, RAND_MAX))
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    print "Sent: ", message
message = "0"
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
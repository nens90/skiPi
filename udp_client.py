import socket

UDP_IP = "10.0.0.23"
UDP_PORT = 5005
MSG_MAX_LEN = 20
MESSAGE = "Hello, World!"

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT
print "message:", MESSAGE

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
if(len(MESSAGE) < MSG_MAX_LEN):
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
else:
    print("MESSAGE too long. Length: ", len(MESSAGE))
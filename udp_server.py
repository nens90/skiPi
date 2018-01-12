import socket

UDP_IP = "10.0.0.23"
UDP_PORT = 5005
MSG_MAX_LEN = 20

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(MSG_MAX_LEN) # buffer size is 20 bytes
    print "received message:", data
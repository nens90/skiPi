#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase

import threading

import struct
import fcntl
import select
import socket


# ============================= Kesselfall Network ==========================
# ----------------------------- Configuration -------------------------------
INTERFACE_DEFAULT = "wlan0"

MCAST_GRP = '224.0.8.1'
MCAST_TTL = struct.pack('b', 1)
MCAST_PORT_DEFAULT = 5005
MCAST_MSG_MAX_LEN  = 20

KFNET_TTL_RETRANS = 5           # How many application-layer retransmissionss
KFNET_TTL_TIMEOUT_MS = 10000    # ms before received information is wiped


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

# ----------------------------- Multicast -----------------------------------
class McastSender(socket.socket):
    def __init__(self, interface, mcast_grp, mcast_port):
        super().__init__( socket.AF_INET,
                          socket.SOCK_DGRAM,
                          socket.IPPROTO_UDP )
        # Set TTL to 1. (Restricted to same subnet)
        self.setsockopt( socket.IPPROTO_IP,
                         socket.IP_MULTICAST_TTL,
                         MCAST_TTL)
        # Specify interface
        self.setsockopt(socket.SOL_SOCKET, 25, interface.encode())
        self.mcast_grp = mcast_grp
        self.to_port = mcast_port
        
    def mcast_send(self, data):
        self.sendto((data + '\0').encode(), (self.mcast_grp, self.to_port))
        skibase.log_debug("Sent: %s" %data)

  
        
class McastListener(socket.socket):
   def __init__(self, mcast_grp, ip_addr, mcast_port):
        super().__init__( socket.AF_INET, 
                          socket.SOCK_DGRAM, 
                          socket.IPPROTO_UDP )
        # Set socket to non-blocking
        self.setblocking(0)
        # Allow multiple liseners on the same port
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to port
        self.bind(('', mcast_port))
        # Inform kernel that "we" are listining for multicasts
        # (membership is dropped again when the socket close)
        mreq = socket.inet_pton(socket.AF_INET, mcast_grp) + \
               struct.pack( "=4s", socket.inet_aton(ip_addr))
        self.setsockopt(
          socket.IPPROTO_IP,
          socket.IP_ADD_MEMBERSHIP,
          mreq
        )


   def mcast_check_receive(self):
        ready = select.select([self], [], [], 0.010) # Non-blocking, 10 ms
        if ready[0]:
            data, addr = self.recvfrom(MCAST_MSG_MAX_LEN)
            if data:
                skibase.log_debug("Received: %s" %data.decode())
                return data
        return None


# ----------------------------- Protocol ------------------------------------
class KesselfallNetwork(threading.Thread):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, interface, mcast_grp, ip_addr, mcast_port):
        super().__init__()
        self._stop_event = threading.Event()
        self.mcast_sender_obj = McastSender( interface,
                                             mcast_grp,
                                             mcast_port )
        self.mcast_listener_obj = McastListener( mcast_grp,
                                                 ip_addr,
                                                 mcast_port )
        
    def status(self):
        return self.is_alive()
        
    def run(self):
        counter = 0
        while counter < 5:
            counter += 1
            self._send("%d" %counter)
            skibase.log_debug("%d" %counter)
            for i in range(10):
                self._receive()
                time.sleep(0.2)
            if self._got_stop_event():
                break
                   
    def stop(self):
        self._stop_event.set()

    def _got_stop_event(self):
        return self._stop_event.is_set()
        
    # === Send / Receive ===
    def _send(self, data):
        self.mcast_sender_obj.mcast_send(data)
        
    def _receive(self):
        return self.mcast_listener_obj.mcast_check_receive()

        
# ----------------------------- Handling ------------------------------------
def kfnet_start(interface, mcast_grp, ip_addr, mcast_port):
    # Find IP address if set to "auto"
    if ip_addr == "auto":
        ip_addr = get_ip_address(interface)
        skibase.log_info("Found IP address: %s" %ip_addr)
    # Start KesselfallNetwork
    kfnet_obj = KesselfallNetwork(interface, mcast_grp, ip_addr, mcast_port)
    kfnet_obj.setName("KesselfallNetwork")
    kfnet_obj.daemon = True
    kfnet_obj.start()
    return kfnet_obj

    
def kfnet_stop(kfnet_obj):
    # If still alive; stop
    if kfnet_obj.status():
        kfnet_obj.stop()
        kfnet_obj.join()



# ============================= argparse ====================================
def args_add_kfnet(parser):
    # interface
    parser.add_argument(
      '-i', '--interface',
      type=str,
      action="store",
      dest="interface",
      default=INTERFACE_DEFAULT,
      help="Specify interface. Default: %s" %INTERFACE_DEFAULT
    )
    # ip
    parser.add_argument(
      '-a', '--addr',
      type=str,
      action="store",
      dest="ip_addr",
      default="auto",
      help="Specify listen IP raddress. Default: \'auto\'"
    )
    # port
    parser.add_argument(
      '-p', '--port',
      type=int,
      action="store",
      dest="mcast_port",
      default=MCAST_PORT_DEFAULT,
      help="Specify UDP listen port. Default: %d" %MCAST_PORT_DEFAULT
    )
    return parser
    
    
    
# ============================= Unittest ====================================
CHANGE_RATE = 2.5

def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_kfnet(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Start kfnet
    kfnet_obj = kfnet_start( args.interface,
                             MCAST_GRP, 
                             args.ip_addr,
                             args.mcast_port)
    
    # Loop (main)
    skibase.log_info("Running Kesselfall network unittest")
    while not skibase.signal_counter and kfnet_obj.status():
        skibase.log_debug(".", end='')
        time.sleep(0.8)
        
    kfnet_obj = kfnet_stop(kfnet_obj)

    skibase.log_info("Kesselfall network unittest ended")

    
if __name__ == '__main__':
    test()

#EOF
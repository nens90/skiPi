#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import threading
import struct
import fcntl
import select
import socket
#import secrets
import random
import ctypes
import string
import queue

import skibase


KFNET_RETRANS_PROBABILITY = 190 # Probablitity of retransmission (0-255)
KFNET_TTL_RETRANS = 5 # How many application-layer retransmissionss
KFNET_DATA_MAX_LEN = 50
KFNET_PACKET_ID_LEN = 4
KFNET_PACKET_TIMEOUT_MS = 10000 # ms before received information is wiped

MCAST_INTERFACE_DEFAULT = "wlan0"
MCAST_GRP = '224.0.8.1'
MCAST_TTL = struct.pack('b', 1)
MCAST_PORT_DEFAULT = 5005
MCAST_PACKET_MAX_LEN  = (KFNET_PACKET_ID_LEN 
                        + 1 + 1 + 2 + 1
                        + KFNET_DATA_MAX_LEN
                        + 1)

ALPHABET = string.ascii_letters + string.digits


# ============================= Common ======================================
def generate_packet_id():
    return ''.join(random.choice(ALPHABET) for i in range(KFNET_PACKET_ID_LEN))

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
                            fcntl.ioctl(
                                        s.fileno(),
                                        0x8915,  # SIOCGIFADDR
                                        struct.pack('256s',
                                                    ifname[:15].encode()
                                        )
                            )[20:24]
    )

    
# ============================= Kesselfall Network ==========================
# ----------------------------- Multicast -----------------------------------
class McastSender(socket.socket):
    def __init__(self, interface, mcast_grp, mcast_port):
        super().__init__(socket.AF_INET,
                         socket.SOCK_DGRAM,
                         socket.IPPROTO_UDP)
        # Set TTL to 1. (Restricted to same subnet)
        self.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        MCAST_TTL)
        # Specify interface
        self.setsockopt(socket.SOL_SOCKET, 25, interface.encode())
        # Do not loop back own messages
        self.setsockopt(socket.SOL_IP,
                        socket.IP_MULTICAST_LOOP,
                        0)
        self.mcast_grp = mcast_grp
        self.to_port = mcast_port
        
    def mcast_send(self, data):
        self.sendto(data,
                    (self.mcast_grp, self.to_port))
        packet_hex_str = ' '.join(format(x, '02x') for x in data)
        skibase.log_debug("Sent %d bytes: %s" %(len(data),
                                                packet_hex_str))

  
        
class McastListener(socket.socket):
   def __init__(self, mcast_grp, ip_addr, mcast_port):
        super().__init__(socket.AF_INET, 
                         socket.SOCK_DGRAM, 
                         socket.IPPROTO_UDP)
        # Set socket to non-blocking
        self.setblocking(0)
        # Allow multiple liseners on the same port
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to port
        self.bind(('', mcast_port))
        # Inform kernel that "we" are listining for multicasts
        # (membership is dropped again when the socket close)
        mreq = socket.inet_pton(socket.AF_INET, mcast_grp) \
               + struct.pack( "=4s", socket.inet_aton(ip_addr))
        self.setsockopt(socket.IPPROTO_IP,
                        socket.IP_ADD_MEMBERSHIP,
                        mreq)

   def mcast_check_receive(self):
        ready = select.select([self], [], [], 0.010) # Non-blocking, 10 ms
        if ready[0]:
            data, addr = self.recvfrom(MCAST_PACKET_MAX_LEN)
            if data:
                data_hex_str = ' '.join(format(x, '02x') for x in data)
                skibase.log_debug(("Received %d bytes: %s") \
                                   % (len(data), data_hex_str))
                return data
        return None


# ----------------------------- Protocol ------------------------------------
class KesselfallHeader(ctypes.LittleEndianStructure):
    _fields_ = [
      ("id", ctypes.c_char * KFNET_PACKET_ID_LEN),  # Packet ID
      ("ttl", ctypes.c_uint8),  # Packet TTL
      ("rp", ctypes.c_uint8),  # Probablitity to resend received packet
      ("type", ctypes.c_uint16),  # Type of data
      ("len", ctypes.c_uint8),  # Length of data
      ("data", ctypes.c_char * KFNET_DATA_MAX_LEN)  # Data
    ]
    

class KesselfallNetwork(threading.Thread):
    """
    TODO
    """
    
    _received_packet_ids = list()
    
    # === Thread handling ===
    def __init__(self, interface, mcast_grp, ip_addr, mcast_port):
        super().__init__()
        self._stop_event = threading.Event()
        self.init_network(interface, mcast_grp, ip_addr, mcast_port)
        self.to_network_queue = queue.Queue()
        
    def status(self):
        return self.is_alive()
        
    def run(self):
        while True:
            # Send to network (from queue)
            while self.to_network_queue.empty() is False:
                packet = self.to_network_queue.get()
                self._send(packet)
                self.to_network_queue.task_done()
            # Receive from network (to queue)
            packet = self._receive()
            if self._got_stop_event():
                break
                   
    def stop(self):
        self._stop_event.set()

    def _got_stop_event(self):
        return self._stop_event.is_set()
        
    # === Network ===
    def init_network(self, interface, mcast_grp, ip_addr, mcast_port):
        skibase.log_info("Initializing Kesselfall network.")
        self.mcast_sender_obj = McastSender(interface,
                                            mcast_grp,
                                            mcast_port)
        self.mcast_listener_obj = McastListener(mcast_grp,
                                                ip_addr,
                                                mcast_port)

    # --- Send ---
    # queue serve
    
    def _send(self, packet):
        # Verify packet
        if len(bytes(packet)) > MCAST_PACKET_MAX_LEN:
            skibase.log_notice(("Discard packet ID '%s'. Packet is %d/%d bytes long") \
                                 %(packet.id.decode(),
                                 len(bytes(packet)),
                                 MCAST_PACKET_MAX_LEN))
            return
        # Check if we will resend packet
        number = random.randint(0x00, 0xFF)
        if packet.rp < number:
            skibase.log_debug(("Discard resend of packet ID '%s' (%d < %d)") \
                              %(packet.id.decode(), packet.rp, number))
            return
        # Decrease TTL
        packet.ttl -= 1
        if packet.ttl < 1:
            skibase.log_debug(("Discard packet ID '%s'. TTL is %d") \
                              %(packet.id.decode(), packet.ttl))
            return
        # Send
        self.mcast_sender_obj.mcast_send(bytes(packet))

    # --- Receive ---
    def _receive(self):
        data = self.mcast_listener_obj.mcast_check_receive()
        if data is not None:
            # On an ad-hoc mesh network we will probably receive the
            # same packet multiple times. We will only store each
            # packet (packet ID) for a short time, and then discard
            # it in case of an "rereceived" packet.
            packet = KesselfallHeader.from_buffer_copy(data)
            t_now = skibase.get_time_ms()
            t_timeout = t_now + KFNET_PACKET_TIMEOUT_MS
            for i, [p_to, p_id] in enumerate(self._received_packet_ids[:]):
                # Check if p_to for p_id is timed out
                if p_to < t_now:
                    skibase.log_debug(
                      ("Removing packet ID '%s' with timeout %d.") \
                      % (packet.id.decode(), p_to))
                    self._received_packet_ids.remove([p_to, p_id])
                    continue
                # Check if this packet was already received.
                if packet.id == p_id:
                    # Renew timeout
                    skibase.log_debug(
                      "Renewing timout of packet ID '%s' from %d to %d." \
                      % (packet.id.decode(), p_to, t_timeout))
                    self._received_packet_ids[i] = [t_timeout, p_id]
                    return None
            # We have identified a new packet
            # Send packet and add it to the list of _received_packet_ids
            self._send(packet)  # Prioritize send
            self._received_packet_ids.append([t_timeout, packet.id])
            skibase.log_debug(
              "Received packet '%s' with timeout: %d." \
              % (packet.id.decode(), t_timeout))
            return packet
        return None

        
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
      default=MCAST_INTERFACE_DEFAULT,
      help="Specify interface. Default: %s" %MCAST_INTERFACE_DEFAULT
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
    skibase.set_time_start()

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
    kfnet_obj = kfnet_start(args.interface,
                            MCAST_GRP, 
                            args.ip_addr,
                            args.mcast_port)
    
    # Loop (main)
    skibase.log_notice("Running Kesselfall network unittest")
    counter = 0
    while not skibase.signal_counter and kfnet_obj.status():
        packet = KesselfallHeader()
        packet.id = generate_packet_id().encode()
        packet.ttl = KFNET_TTL_RETRANS
        packet.rp = KFNET_RETRANS_PROBABILITY
        packet.type = 0x1337
        packet.data = ("Hello world: %d" %counter).encode()
        packet.len = len(packet.data)
        kfnet_obj.to_network_queue.put(packet)
        skibase.log_debug(".", end='')
        time.sleep(0.8)
        counter += 1
        
    kfnet_obj = kfnet_stop(kfnet_obj)

    skibase.log_notice("Kesselfall network unittest ended")

    
if __name__ == '__main__':
    test()

#EOF
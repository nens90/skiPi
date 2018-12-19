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
import random
import ctypes
import string
import queue

import skibase


KFNET_RETRANS_PROBABILITY = 190 # Probablitity of retransmission (0-255)
KFNET_TTL_RETRANS = 5 # How many application-layer retransmissionss
KFNET_DATA_MAX_LEN = 4
KFNET_PACKET_ID_LEN = 4
KFNET_PACKET_TIMEOUT_MS = 10000 # ms before received information is wiped
KFNET_STX = 0x51
KFNET_ETX = 0xE1

MCAST_INTERFACE_DEFAULT = "wlan0"
MCAST_GRP = '224.0.8.1'
MCAST_TTL = struct.pack('b', 1)
MCAST_PORT_DEFAULT = 5005
MCAST_PACKET_LEN  = (
  1  # stx
  +  KFNET_PACKET_ID_LEN  # id 
  + 2  # src
  + 1  # ttl
  + 1  # rp
  + KFNET_DATA_MAX_LEN  # data
  + 1  # etx
)

ALPHABET = string.ascii_letters + string.digits


# ============================= Common ======================================
def generate_packet_id():
    return ''.join(random.choice(ALPHABET) for i in range(KFNET_PACKET_ID_LEN))
    
def generate_source_id():
    return random.randint(1, (2**16)-1)
    
def bytes_to_hex_str(bytes_object):
    return ' '.join(format(x, '02x') for x in bytes_object)

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
        skibase.log_debug("Sent %d bytes: \n%s" %(len(data),
                                                  bytes_to_hex_str(data)))

  
        
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
        ready = select.select([self], [], [], 0.100) # Non-blocking, 100 ms
        if ready[0]:
            data, addr = self.recvfrom(MCAST_PACKET_LEN)
            if data:
                skibase.log_debug(("Received %d bytes: \n%s") \
                                   % (len(data), bytes_to_hex_str(data)))
                return data
        return None


# ----------------------------- Protocol ------------------------------------
class KesselfallHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
      ("stx", ctypes.c_uint8),  # Start byte
      ("id", ctypes.c_char * KFNET_PACKET_ID_LEN),  # Packet ID
      ("src", ctypes.c_uint16),  # Source ID (who originally created packet)
      ("ttl", ctypes.c_uint8),  # Packet TTL
      ("rp", ctypes.c_uint8),  # Probablitity to resend received packet
      ("data", ctypes.c_char * KFNET_DATA_MAX_LEN),  # Data
      ("etx", ctypes.c_uint8),  # End byte
    ]
    

class KesselfallNetwork(threading.Thread):
    """
    TODO
    """
    
    _known_packet_ids = list()
    
    # === Thread handling ===
    def __init__(self, main_queue,
                 interface, mcast_grp, ip_addr, mcast_port):
        super().__init__()
        self._main_queue = main_queue
        self._queue = queue.Queue()
        self.source_id = generate_source_id()
        self.mcast_sender_obj = McastSender(interface,
                                            mcast_grp,
                                            mcast_port)
        self.mcast_listener_obj = McastListener(mcast_grp,
                                                ip_addr,
                                                mcast_port)
        self._stop_event = threading.Event()
        
        
    def status(self):
        return self.is_alive()
                   
    def stop(self):
        self._stop_event.set()

    def _got_stop_event(self):
        return self._stop_event.is_set()
        
    # --- Loop ---
    def run(self):
        t_next = skibase.get_time_millis() + KFNET_PACKET_TIMEOUT_MS
        while not self._got_stop_event():
            # Send to network (from queue)
            while self._queue.empty() is False:
                packet = self._queue.get()
                self._send(packet)
                self._queue.task_done()
            # Receive from network (to queue)
            packet = self._receive() # blocking
            if packet is not None:
                self._main_queue.put(packet)
            # Check if p_to for p_id is timed out (once every X ms)
            t_now = skibase.get_time_millis()
            if t_now > t_next:
                for [p_to, p_id] in self._known_packet_ids[:]:
                    if p_to < t_now:
                        skibase.log_debug(
                          ("Removing packet ID '%s' with timeout %d.") \
                          % (p_id.decode(), p_to))
                        self._known_packet_ids.remove([p_to, p_id])
                t_next = t_next + 1000
        # Empty queue and stop
        while self._queue.empty() is False:
            self._queue.get()
            self._queue.task_done()
            
    # === Queue ===
    def queue_data(self, data_string):
        packet = self.create_packet()
        packet.data = data_string.encode()
        self.queue_packet(packet)
        
    def queue_packet(self, packet):
        self._queue.put(packet)
        
    # === Network ===
    # --- Send ---
    # queue serve
    def create_packet(self):
        # Fill packet with default stuff
        packet = KesselfallHeader()
        packet.stx = KFNET_STX
        packet.id = generate_packet_id().encode()
        packet.src = self.source_id
        packet.ttl = KFNET_TTL_RETRANS
        packet.rp = KFNET_RETRANS_PROBABILITY
        packet.etx = KFNET_ETX
        # Add packet to _known_packet_ids
        t_timeout = skibase.get_time_millis() + KFNET_PACKET_TIMEOUT_MS
        self._known_packet_ids.append([t_timeout, packet.id])
        return packet
    
    def _send(self, packet):
        # Check STX and ETX
        if packet.stx != KFNET_STX or packet.etx != KFNET_ETX:
            skibase.log_warning(("Invalid packet: \n%s") \
                                %(bytes_to_hex_str(data)))
            return
        # Verify length
        if len(bytes(packet)) != MCAST_PACKET_LEN:
            skibase.log_warning(("Packet ID '%s'. Packet is %d/%d bytes long") \
                                 %(packet.id.decode(),
                                 len(bytes(packet)),
                                 MCAST_PACKET_LEN))
            return
        # Check if we will resend packet (if not new packet)
        number = random.randint(0x00, 0xFF)
        if packet.rp < number and packet.ttl != KFNET_TTL_RETRANS:
            skibase.log_debug(("Discard resend of packet ID '%s' (%d < %d)") \
                              %(packet.id.decode(), packet.rp, number))
            return
        # Decrease TTL
        if packet.ttl < 1:
            skibase.log_debug(("Discard packet ID '%s'. TTL is %d") \
                              %(packet.id.decode(), packet.ttl))
            return
        packet.ttl -= 1
        # Send
        self.mcast_sender_obj.mcast_send(bytes(packet))
        skibase.log_info(("Sent packet ID '%s'. TTL is %d") \
                         %(packet.id.decode(), packet.ttl+1))

    # --- Receive ---
    def _receive(self):
        data = self.mcast_listener_obj.mcast_check_receive()
        if data is not None:
            # On an ad-hoc mesh network we will probably receive the
            # same packet multiple times. We will only store each
            # packet (packet ID) for a short time, and then discard
            # it in case of an "rereceived" packet.
            packet = KesselfallHeader.from_buffer_copy(data)
            # Check if packet was sent by ourselves
            if packet.src == self.source_id:
                return None
            # Check packet is valid
            if packet.stx != KFNET_STX or packet.etx != KFNET_ETX:
                skibase.log_warning(("Invalid packet: \n%s") \
                                %(bytes_to_hex_str(data)))
                return None
            t_timeout = skibase.get_time_millis() + KFNET_PACKET_TIMEOUT_MS
            for i, [p_to, p_id] in enumerate(self._known_packet_ids[:]):
                # Check if this packet was already received.
                if packet.id == p_id:
                    # Renew timeout
                    skibase.log_debug(
                      "Renewing timout of packet ID '%s' from %d to %d." \
                      % (packet.id.decode(), p_to, t_timeout))
                    self._known_packet_ids[i] = [t_timeout, p_id]
                    return None
            # We have identified a new packet
            # Send packet and add it to the list of _known_packet_ids
            skibase.log_info(
              "Received packet '%s' with timeout: %d." \
              % (packet.id.decode(), t_timeout))
            self._send(packet)  # Prioritize send (TODO)
            self._known_packet_ids.append([t_timeout, packet.id])
            return packet
        return None

        
# ----------------------------- Handling ------------------------------------
def kfnet_start(main_queue, interface,
                mcast_grp, ip_addr, mcast_port):
    # Find IP address if set to "auto"
    if ip_addr == "auto":
        ip_addr = get_ip_address(interface)
        skibase.log_info("Found IP address: %s" %ip_addr)
    # Start KesselfallNetwork
    kfnet_obj = KesselfallNetwork(main_queue, interface,
                                  mcast_grp, ip_addr, mcast_port)
    kfnet_obj.setName("KesselfallNetwork")
    kfnet_obj.daemon = True
    kfnet_obj.start()
    return kfnet_obj

    
def kfnet_stop(kfnet_obj):
    # If still alive; stop
    if kfnet_obj.status():
        kfnet_obj.stop()
        kfnet_obj._queue.join()
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
CHANGE_RATE_MIN = 20
CHANGE_RATE_MAX = 20000

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

    # Start queue
    main_queue = queue.Queue()

    # Start kfnet
    kfnet_obj = kfnet_start(main_queue,
                            args.interface,
                            MCAST_GRP, 
                            args.ip_addr,
                            args.mcast_port)

    # Loop (main)
    skibase.log_notice("Running Kesselfall network unittest")
    counter = 0
    t_next_send = skibase.get_time_millis()
    while not skibase.signal_counter and kfnet_obj.status():
        try:
            data = main_queue.get(block=True, timeout=0.25)
        except queue.Empty:
            data = None
        if data is not None:
            try:
                packet = KesselfallHeader.from_buffer_copy(data)
                skibase.log_notice("-> Packet: %s :: data: %s" %\
                  (packet.id.decode(), packet.data.decode()))
            except:
                skibase.log_warning("kfnet got unknown data")
            main_queue.task_done()
        if t_next_send < skibase.get_time_millis():
            # Send packet to kfnet task
            # otherwise use kfnet_obj.queue_data(data)
            packet = kfnet_obj.create_packet()
            packet.data = (("%d" %(counter%10)) * KFNET_DATA_MAX_LEN).encode()
            kfnet_obj.queue_packet(packet)
            skibase.log_notice("<- Packet: %s :: data: %s" %\
              (packet.id.decode(), packet.data.decode()))
            t_next_send = t_next_send \
                          + random.randint(CHANGE_RATE_MIN, CHANGE_RATE_MAX)
            counter += 1
        
    kfnet_obj = kfnet_stop(kfnet_obj)

    skibase.log_notice("Kesselfall network unittest ended")

    
if __name__ == '__main__':
    test()

#EOF
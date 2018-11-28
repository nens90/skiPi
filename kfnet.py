#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase

import select
import socket


# ============================= Kesselfall Network ==========================
# ----------------------------- Configuration -------------------------------
UDP_PORT_DEFAULT = 5005
UDP_MSG_MAX_LEN  = 20



# ============================= argparse ====================================
def args_add_kfnet(parser):
    # ip
    parser.add_argument( '-a', '--ip',
                         type=str,
                         action="store",
                         dest="ipaddress",
                         default="auto",
                         help="Specify IP address.")
    # port
    parser.add_argument( '-p', '--port',
                         type=int,
                         action="store",
                         dest="udpport",
                         default=UDP_PORT_DEFAULT,
                         help="Specify UDP listen port.")
    return parser
    
    
    
# ============================= Main ========================================
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
    
    while not skibase.signal_counter:
        skibase.log_info(".", end='')
        time.sleep(0.8)

    
if __name__ == '__main__':
    test()

#EOF
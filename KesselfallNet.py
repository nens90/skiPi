#!/usr/bin/env python3
"""
TODO
"""

import argparse

import time
import select
import socket



UDP_PORT_DEFAULT = 5005
UDP_MSG_MAX_LEN  = 20



# ============================= argparse ====================================
def args_add(parser):
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
    
#EOF

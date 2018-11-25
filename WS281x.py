#!/usr/bin/env python3
"""
TODO
"""

import argparse

import time



LED_PIN_DEFAULT = 18



# ============================= argparse ====================================
def args_add(parser):
    # ledpin
    parser.add_argument( '-l', '--pin',
                         type=int,
                         action="store",
                         dest="ledpin",
                         default=LED_PIN_DEFAULT,
                         help="Set pin number that the data pin of the LED strip is connected to.")
    # ledtype
    
    return parser
    
#EOF

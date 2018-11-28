#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase

import board
import neopixel



# ============================= NeoPixel ====================================
# ----------------------------- Configuration -------------------------------
LED_PIN_DEFAULT = 18



# ============================= argparse ====================================
def args_add_ws281x(parser):
    # ledpin
    parser.add_argument( '-l', '--pin',
                         type=int,
                         action="store",
                         dest="ledpin",
                         default=LED_PIN_DEFAULT,
                         help="Set pin number that the data pin of the LED strip is connected to.")
    # ledtype
    
    return parser



# ============================= Main ========================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_ws281x(parser)
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

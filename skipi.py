#!/usr/bin/env python3
"""
skipi is a project for synchronization of WS281x LED strips (aka NeoPixels) 
over an ad-hoc network connection.
"""

import sys
import time
import argparse
import signal

import skibase

import wd
import kfnet
import ws281x



# ============================= argparse ====================================   
def args_add_all(parser):
    # === Logging ===
    parser = skibase.args_add_log(parser)
    # === Watchdog ===
    parser = wd.args_add_wd(parser)
    # === Network ===
    parser = kfnet.args_add_kfnet(parser)
    # === WS281x ===
    parser = ws281x.args_add_ws281x(parser)
    # === Tests ===
    # nettest
    parser.add_argument( '--nettest',
                         action="store_true",
                         dest="nettest",
                         default=False,
                         help="Run network-only test; Execute Kesselfall network without WS281x handling.")
    # ledtest
    parser.add_argument( '--ledtest',
                         action="store_true",
                         dest="ledtest",
                         default=False,
                         help="Run LED-only test; Execute WS281x without Kesselfall network handling.")

    return parser

    
    
# ============================= Main ========================================

# ----------------------------- Loop ----------------------------------------
LOOP_SPEED = 0.8

def loop():
    next_kick = 0
    
    while not skibase.signal_counter:
        next_kick = wd.wd_check(next_kick)
        time.sleep(LOOP_SPEED)



# ---------------------------------------------------------------------------
def main():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = args_add_all(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Watchdog
    wd.wd_set_handle(args.watchdog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd.wd_kick()
    
    # Start LED strip (WS281x)
    
    # Start the Kesselfall network protocol
    
    skibase.log_info("Running skipi")
    loop()
    skibase.log_info("\nskipi ended...")

    
if __name__ == '__main__':
    main()

#EOF

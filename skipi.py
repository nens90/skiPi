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

import kfnet
import ws281x
    

    
# ============================= Watchdog ====================================
WD_DEVICE = "/dev/watchdog"
WD_INTERVAL = 15

WD_HANDLE_DEFAULT = True
wd_handle = WD_HANDLE_DEFAULT

WD_SAFETY = 1250


def wd_kick():
    if wd_handle:
        with open(WD_DEVICE, 'w') as wd_fd:
            wd_fd.write('1')
        #skibase.log_debug(".", end='')

def wd_check(next_kick):
    time_ms = skibase.get_time_millis()
    if time_ms >= next_kick or next_kick == 0:
        wd_kick()
        next_kick = time_ms + (WD_INTERVAL * 1000) - WD_SAFETY
    return next_kick
            
def wd_set_handle(handle):
    global wd_handle
    wd_handle = handle
    skibase.log_debug("Set watchdog handle to: %s" %handle)
    
    

# ============================= argparse ====================================   
def args_add_all(parser):
    # === Logging ===
    parser = skibase.args_add_log(parser)
    # === Watchdog ===
    # watchdog
    parser.add_argument( '-w', '--nowd',
                         action="store_false",
                         dest="watchdog",
                         default=WD_HANDLE_DEFAULT,
                         help="Do not kick the watchdog; Disable watchdog handling.")
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
    skibase.log_info("Running main-loop")
    next_kick = 0
    
    while not skibase.signal_counter:
        next_kick = wd_check(next_kick)
        time.sleep(LOOP_SPEED)
        
    skibase.log_info("\nmain-loop ended...")
        
        
        
# ---------------------------------------------------------------------------
def main():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = args_add_all(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Watchdog
    wd_set_handle(args.watchdog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd_kick()
    
    # Start LED strip (WS281x)
    
    # Start the Kesselfall network protocol
    
    loop()

    
if __name__ == '__main__':
    main()

#EOF

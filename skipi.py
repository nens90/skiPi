#!/usr/bin/env python3
"""
skipi is a project for synchronization of WS281x LED strips (aka NeoPixels) 
over an ad-hoc network connection.
"""

import sys
import time
import argparse
import signal
import queue

import skibase

import wd
import kfnet
import ws281x
import sphat



# ============================= argparse ====================================   
def args_add_all(parser):
    # === Logging ===
    parser = skibase.args_add_log(parser)
    # === Watchdog ===
    parser = wd.args_add_wd(parser)
    # === Kesselfall Network ===
    parser = kfnet.args_add_kfnet(parser)
    # === WS281x ===
    parser = ws281x.args_add_ws281x(parser)
    # === Scroll PHAT ===
    parser = sphat.args_add_sphat(parser)
    # === Tests ===
    # nettest
    #parser.add_argument( 
    #  '--nettest',
    #  action="store_true",
    #  dest="nettest",
    #  default=False,
    #  help="Run network-only test; (not supported yet)"
    #)
    # ledtest
    #parser.add_argument( 
    #  '--ledtest',
    #  action="store_true",
    #  dest="ledtest",
    #  default=False,
    #  help="Run LED-only test; (not supported yet)"
    #)
    # ledtest
    #parser.add_argument(
    #  '--sphattest',
    #  action="store_true",
    #  dest="sphattest",
    #  default=False,
    #  help="Run sphat-only test; (not supported yet)"
    #)

    return parser

    
    
# ============================= Main ========================================

# ----------------------------- Loop ----------------------------------------
LOOP_SPEED = 0.8

def loop(main_queue, kfnet_obj):
    next_kick = 0
    
    while not skibase.signal_counter and kfnet_obj.status():
        next_kick = wd.wd_check(next_kick)
        try:
            data = main_queue.get(block=True, timeout=LOOP_SPEED)
        except queue.Empty:
            data = None
        if data is not None:
            try:
                packet = kfnet.KesselfallHeader.from_buffer_copy(data)
                skibase.log_notice("-> Packet: %s :: data: %s" %\
                  (packet.id.decode(), packet.data.decode()))
            except:
                skibase.log_warning("main got unknown data from kfnet")
            main_queue.task_done()


# ---------------------------------------------------------------------------
def main():
    skibase.set_time_start()
    
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
    
    # Start queue
    main_queue = queue.Queue()
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd.wd_kick()
    
    # Start scroll phat

    # Start LED strip (WS281x)
    
    # Start the Kesselfall network protocol
    kfnet_obj = kfnet.kfnet_start(main_queue,
                                  args.interface,
                                  kfnet.MCAST_GRP, 
                                  args.ip_addr,
                                  args.mcast_port)
                                  
    # Start button
    

    # Run
    skibase.log_notice("Running skipi")
    loop(main_queue, kfnet_obj)
    
    # Stop
    kfnet_obj = kfnet.kfnet_stop(kfnet_obj)
    skibase.log_notice("\nskipi ended...")
    
    
if __name__ == '__main__':
    main()

#EOF

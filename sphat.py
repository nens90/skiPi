#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase



# ============================= Scroll PHAT =================================
# ----------------------------- Configuration -------------------------------


# ============================= argparse ====================================
def args_add_sphat(parser):
    
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_sphat(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Loop
    skibase.log_info("Running Scroll PHAT unittest")
    while not skibase.signal_counter:
        skibase.log_info(".", end='')
        time.sleep(0.8)

    skibase.log_info("Scroll PHAT unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

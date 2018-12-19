#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase

    
# ============================= Watchdog ====================================
WD_DEVICE = "/dev/watchdog"
WD_INTERVAL_SEC = 15

WD_ENABLED_DEFAULT = True
wd_enabled = WD_ENABLED_DEFAULT

WD_GUARD_TIME_MS = 1250


def wd_kick():
    if wd_enabled:
        try:
            with open(WD_DEVICE, 'w') as wd_fd:
                wd_fd.write('1')
        except:
            skibase.die_err("Cannot kick watchdog. Ensure that the you "   \
            "execute as root (permissions) and that the watchdog device "  \
            "is free.")
            
        skibase.log_debug("!", end='')

def wd_check(next_kick):
    time_ms = skibase.get_time_millis()
    if time_ms >= next_kick or next_kick == 0:
        wd_kick()
        next_kick = time_ms + (WD_INTERVAL_SEC * 1000) - WD_GUARD_TIME_MS
    return next_kick
            
def wd_set_handle(handle):
    global wd_enabled
    wd_enabled = handle
    skibase.log_debug("Set watchdog handle to: %s" %handle)
    
    

# ============================= argparse ====================================
def args_add_wd(parser):
    # watchdog disable
    parser.add_argument(
      '-w', '--nowd',
      action="store_false",
      dest="watchdog",
      default=WD_ENABLED_DEFAULT,
      help="Do not kick the watchdog; Disable watchdog handling."
    )
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_wd(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Watchdog
    wd_set_handle(args.watchdog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd_kick()
    
    # Loop
    skibase.log_notice("Running watchdog unittest")
    next_kick = 0
    while not skibase.signal_counter:
        next_kick = wd_check(next_kick)
        skibase.log_info(".", end='')
        time.sleep(0.8)
        
    skibase.log_notice("\nWatchdog unittest ended...")

    
if __name__ == '__main__':
    test()



#EOF

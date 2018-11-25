#!/usr/bin/env python3
"""
skipi is a project for synchronization of WS281x LED strips (aka NeoPixels) 
over an ad-hoc network connection.
"""

import sys
import time
import signal
import argparse

import syslog

import KesselfallNet
import WS281x



# ============================= Common ======================================
def die_err(msg):
    log_error(msg)
    sys.exit(1)
    
    
def get_time_millis():
    return int(round(time.time() * 1000))
    
    
    
# ============================= Logging =====================================
LOG_LEVELS = {
  "DEBUG"  : 1,
  "INFO"   : 2,
  "NOTICE" : 3,
  "WARNING": 4,
  "ERROR"  : 5
}

LOG_SYSLOG = {
  "DEBUG"  : syslog.LOG_DEBUG,
  "INFO"   : syslog.LOG_INFO,
  "NOTICE" : syslog.LOG_NOTICE,
  "WARNING": syslog.LOG_WARNING,
  "ERROR"  : syslog.LOG_ERR
}

LOG_COLORS = {
  "DEBUG"  : 4,
  "INFO"   : 7,
  "NOTICE" : 2,
  "WARNING": 3,
  "ERROR"  : 1
}

LOG_RESET_SEQ = "\033[0m"
LOG_COLOR_SEQ = "\033[1;%dm"

LOG_LEVEL_DEFAULT = "INFO"
log_level = LOG_LEVELS[LOG_LEVEL_DEFAULT]

log_syslog = False

    
def log_print(msg, level):
    if LOG_LEVELS[level] >= log_level:
        colored_msg = ( LOG_COLOR_SEQ % (30 + LOG_COLORS[level])
                        + msg
                        + LOG_RESET_SEQ )
        sys.stdout.write(colored_msg)
        sys.stdout.flush()
        if log_syslog:
            for line in msg.split('\n'):
                if line != '':
                    syslog.syslog(LOG_SYSLOG[level], level + ": " + line)

def log_debug(msg, end='\n'):
    log_print(msg + end, "DEBUG")

def log_info(msg, end='\n'):
    log_print(msg + end, "INFO")
    
def log_notice(msg, end='\n'):
    log_print(msg + end, "NOTICE")
    
def log_warning(msg, end='\n'):
    log_print(msg + end, "WARNING")

def log_error(msg, end='\n'):
    log_print(msg + end, "ERROR")
    
def log_set_level(level):
    global log_level
    if not level in LOG_LEVELS:
        die_err("Level \"%s\" is not in LOG_LEVELS" %level)
    log_level = LOG_LEVELS[level]
    log_debug("Set log level to: %s" %level)
    
def log_set_syslog(syslog):
    global log_syslog
    log_syslog = syslog
    log_debug("Set syslog to: %s" %syslog)
    
    
    
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
        #log_debug(".", end='')

def wd_check(next_kick):
    time_ms = get_time_millis()
    if time_ms >= next_kick or next_kick == 0:
        wd_kick()
        next_kick = time_ms + (WD_INTERVAL * 1000) - WD_SAFETY
    return next_kick
            
def wd_set_handle(handle):
    global wd_handle
    wd_handle = handle
    log_debug("Set watchdog handle to: %s" %handle)
    
    
    
# ============================= Main ========================================

# ----------------------------- argparse ------------------------------------
def args_get():
    parser = argparse.ArgumentParser(description=__doc__)
    # === Logging ===
    # loglevel
    parser.add_argument( '-d', '--loglevel',
                         type=str,
                         action="store",
                         dest="loglevel",
                         default=LOG_LEVEL_DEFAULT,
                         help="Set log level :: DEBUG, INFO, NOTICE, WARNING, ERROR.")
    # syslog
    parser.add_argument( '--syslog',
                         action="store_true",
                         dest="syslog",
                         default=False,
                         help="Enable logging to syslog.")
    # === Watchdog ===
    # watchdog
    parser.add_argument( '-w', '--nowd',
                         action="store_false",
                         dest="watchdog",
                         default=WD_HANDLE_DEFAULT,
                         help="Do not kick the watchdog; Disable watchdog handling.")
    # === Network ===
    parser = KesselfallNet.args_add(parser)
    # === WS281x ===
    parser = WS281x.args_add(parser)
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

    return parser.parse_args()
    
    
# ----------------------------- Signal --------------------------------------
def signal_handler(signal, frame):
    global app_is_running
    app_is_running = 0
    log_debug("Got signal: %d" %signal )
    
    
# ----------------------------- Loop ----------------------------------------
app_is_running = 1
LOOP_SPEED = 0.8


def loop():
    log_info("Running main-loop")
    next_kick = 0
    
    while app_is_running:
        next_kick = wd_check(next_kick)
        time.sleep(LOOP_SPEED)
        
    log_info("\nmain-loop ended...")
        
        
# ---------------------------------------------------------------------------
def main():
    args = args_get()
    log_set_level(args.loglevel.upper())
    log_set_syslog(args.syslog)
    wd_set_handle(args.watchdog)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd_kick()
    
    # Start LED strip (WS281x)
    
    # Start the Kesselfall network protocol
    
    loop()

    
if __name__ == '__main__':
    main()

#EOF

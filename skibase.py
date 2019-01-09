#!/usr/bin/env python3
"""
TODO
"""

import sys
import time
import signal
import argparse
import syslog
import threading


# ============================= Tasks =======================================
# All tasks must be within range 0x0000 to 0xFFFF.
# This ensures that a task can be sent over the network as a uint32_t value
TASK_MULTIPLEX = 0xFFFF

MAJOR_TASK = 0xFF00
MINOR_TASK = 0x00FF

TASK_BUTTON_PRESS = 0xB077
TASK_BUTTON_LONG_1 = 0xDEAC
TASK_BUTTON_LONG_2 = 0xDEAD
TASK_DELAY_MS = 0xBB00  # multiplex with MINOR_TASK to get actual delay
# About programs:
# To simplify the design programs are sent over the network as tasks.
TASK_PROGRAM = 0xA500  # multiplex with MINOR_TASK to get program

def task_to_str(task):
    return ("%04x" % task)
    
# ============================= Common ======================================
def die_err(msg):
    log_error(msg)
    sys.exit(1)
    
def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))
    
class ThreadModule(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.setName(name)
        self.daemon = True
        self._stop_event = threading.Event()
        
    def status(self):
        return self.is_alive()
                   
    def stop(self):
        self._stop_event.set()

    def _got_stop_event(self):
        return self._stop_event.is_set()

    
# ============================= Time ========================================

time_start = 0
    
def get_time_millis():
    return int(round(time.time() * 1000)) - time_start
    
def set_time_start():
    global time_start
    time_start = get_time_millis()
    
    
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
    
def log_config(level, syslog):
    log_set_level(level)
    log_set_syslog(syslog)

    
    
# ============================= argparse ====================================
def args_add_log(parser):
    # === Logging ===
    # loglevel
    parser.add_argument(
      '-d', '--loglevel',
      type=str,
      action="store",
      dest="loglevel",
      default=LOG_LEVEL_DEFAULT,
      help="Set log level :: DEBUG, INFO, NOTICE, WARNING, ERROR."
    )
    # syslog
    parser.add_argument(
      '--syslog',
      action="store_true",
      dest="syslog",
      default=False,
      help="Enable logging to syslog."
    )
    return parser
    
    
    
# ============================= Signal ======================================
signal_counter = 0

def signal_handler(sig, frame):
    global signal_counter
    signal_counter+=1
    log_debug("Got signal: %d (counter: %d)" %(sig, signal_counter) )

def signal_setup(sigs):
    for sig in sigs:
        signal.signal(sig, signal_handler)



# ============================= Unittest ====================================
def test():
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = args_add_log(parser)
    args = parser.parse_args()
    
    # Logger
    log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Print logging test
    log_debug("Debug")
    log_info("Info")
    log_notice("Notice")
    log_warning("Warning")
    log_error("Error")
    
    # Loop
    log_notice("Running skibase unittest\n")
    counter = 0
    while not signal_counter:
        counter+=1
        log_info("%d" %counter)
        time.sleep(0.8)
        
    log_notice("skibase unittest ended\n")
    
if __name__ == '__main__':
    test()

#EOF

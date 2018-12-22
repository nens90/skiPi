#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import scrollphathd

import skibase


# ============================= Scroll PHAT =================================
SCROLL_RATE_MS = 30
BRIGHTNESS = 0.5

class Sphat(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program):
        super().__init__("Sphat")
        self.program = start_program
        
    # --- Loop ---
    def run(self):
        while not self._got_stop_event():
            last_program = self.program
            if last_program == 0x00:
                scroll_string = "PROG0"
            elif last_program == 0x01:
                scroll_string = "PROG1"
            elif last_program == 0x02:
                scroll_string = "PROG2"
            elif last_program == 0x03:
                scroll_string = "PROG3"
            else:
                scroll_string = "ERROR%d" %last_program
            skibase.log_info("program: %02x" %last_program)
            scrollphathd.clear()
            scrollphathd.write_string(scroll_string,
                                      brightness=BRIGHTNESS)
            while self.program == last_program and not self._got_stop_event():
                scrollphathd.show()
                scrollphathd.scroll()
                time.sleep(SCROLL_RATE_MS / 1000)


# ----------------------------- Handling ------------------------------------
def sphat_start(start_program):
    sphat_obj = Sphat(start_program)
    sphat_obj.start()
    return sphat_obj

    
def sphat_stop(sphat_obj):
    # If still alive; stop
    if sphat_obj.status():
        sphat_obj.stop()
        sphat_obj.join()

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
    
    # sphat
    program = 0
    sphat_obj = sphat_start(program)
    
    # Loop
    skibase.log_notice("Running Scroll PHAT unittest")
    counter = 0
    while not skibase.signal_counter and sphat_obj.status():
        sphat_obj.program = counter%4
        time.sleep(8)
        counter += 1

    sphat_obj = sphat_stop(sphat_obj)
    skibase.log_notice("Scroll PHAT unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

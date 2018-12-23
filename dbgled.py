#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import board
import gpiozero

import skibase


# ============================= DbgLed ======================================
LED_PIN_DEFAULT = board.D5.id


class DbgLed(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program, dbgpin):
        super().__init__("DbgLed")
        self.program = start_program
        self.ledpin = dbgpin
        
    # --- Loop ---
    def run(self):
        led = gpiozero.LED(self.ledpin)
        last_program = self.program
        while not self._got_stop_event():
            if last_program != self.program:
                last_program = self.program
                if last_program & 0x1:
                    led.on()
                else:
                    led.off()
                skibase.log_debug("LED state: %d" %(last_program & 0x1))
            time.sleep(25 / 1000)


# ----------------------------- Handling ------------------------------------
def dbgled_start(start_program, dbgpin):
    dbgled_obj = DbgLed(start_program, dbgpin)
    dbgled_obj.start()
    return dbgled_obj

    
def dbgled_stop(dbgled_obj):
    # If still alive; stop
    if dbgled_obj.status():
        dbgled_obj.stop()
        dbgled_obj.join()


# ============================= argparse ====================================
def args_add_dbgled(parser):
    # ledpin
    parser.add_argument(
      '--dbgpin',
      type=int,
      action="store",
      dest="dbgpin",
      default=LED_PIN_DEFAULT,
      help="Pin number of the debug LED. (Default: %d)" %LED_PIN_DEFAULT
    )
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_dbgled(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # dbgled
    program = 0
    dbgled_obj = dbgled_start(program, args.dbgpin)
    
    # Loop
    skibase.log_notice("Running DbgPin unittest")
    counter = 0
    while not skibase.signal_counter and dbgled_obj.status():
        dbgled_obj.program = counter
        time.sleep(5)
        counter += 1

    dbgled_obj = dbgled_stop(dbgled_obj)
    skibase.log_notice("DbgPin unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

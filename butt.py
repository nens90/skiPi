#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal
import queue
import threading

import gpiozero

import skibase


BUTT_PIN = 26

LONG_PRESS_TIME = 2500


# ============================= Butt ========================================
class Butt(threading.Thread):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, main_queue, start_program_id):
        super().__init__()
        self.setName("Butt")
        self.daemon = True
        self._main_queue = main_queue
        self._stop_event = threading.Event()
        self.program_counter = start_program_id
        
    def status(self):
        return self.is_alive()
                   
    def stop(self):
        self._stop_event.set()

    def _got_stop_event(self):
        return self._stop_event.is_set()
        
    # --- Loop ---
    def run(self):
        button = gpiozero.Button(BUTT_PIN,
                                 pull_up=True)
                                 #bounce_time=0.005
        
        while not self._got_stop_event():
            button.wait_for_press(timeout=0.500)
            if not button.is_pressed:
                continue
            t_press = skibase.get_time_millis()
            
            button.wait_for_release(timeout=(LONG_PRESS_TIME+10)/1000)
            t_release = skibase.get_time_millis()
            
            press_time = t_release - t_press
            
            if press_time >= LONG_PRESS_TIME:
                skibase.log_debug("Long press")
                if button.is_pressed:
                    button.wait_for_release(timeout=None)
            else:
                skibase.log_debug("Press")
                self.program_counter += 1
                data = skibase.program_id_to_str(
                  self.program_counter%(skibase.PROGRAM_ID_MAX+1)
                )
                self._main_queue.put(data)


# ----------------------------- Handling ------------------------------------
def butt_start(main_queue, start_program_id):
    butt_obj = Butt(main_queue, start_program_id)
    butt_obj.start()
    return butt_obj

    
def butt_stop(butt_obj):
    # If still alive; stop
    if butt_obj.status():
        butt_obj.stop()
        butt_obj.join()


# ============================= argparse ====================================
def args_add_butt(parser):
    # Start program
    parser.add_argument(
      '-m', '--program',
      type=int,
      action="store",
      dest="start_program",
      default=skibase.PROGRAM_DEFAULT,
      help="Starting Program ID. Default: %d" %skibase.PROGRAM_DEFAULT
    )
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_butt(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Start queue
    main_queue = queue.Queue()
    
    # Start Butt
    butt_obj = butt_start(main_queue, args.start_program)
    
    # Loop
    skibase.log_notice("Running butt unittest")
    while not skibase.signal_counter and butt_obj.status():
        try:
            data = main_queue.get(block=True, timeout=0.25)
        except queue.Empty:
            data = None
        if data is not None:
            try:
                program_id = skibase.get_program_id_from_str(data)
                skibase.log_notice("# Program ID: %d" %program_id)
            except:
                skibase.log_warning("butt got unknown data")
        
    # Stop Butt
    butt_stop(butt_obj)

    skibase.log_notice("butt unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

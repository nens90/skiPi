#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal
import queue

import gpiozero

import skibase


BUTT_PIN = 26

LONG_PRESS_TIME = 2500


# ============================= Butt ========================================
class Butt(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, main_queue):
        super().__init__("Butt")
        self._main_queue = main_queue
        
    # --- Loop ---
    def run(self):
        button = gpiozero.Button(BUTT_PIN,
                                 pull_up=True)

        while not self._got_stop_event():
            button.wait_for_press(timeout=0.500)
            if not button.is_pressed:
                continue
            t_press = skibase.get_time_millis()
            
            button.wait_for_release(timeout=(LONG_PRESS_TIME+10)/1000)
            t_release = skibase.get_time_millis()
            
            press_time = t_release - t_press
            
            if press_time >= LONG_PRESS_TIME:
                self._main_queue.put(skibase.TASK_BUTTON_LONG)
                skibase.log_debug("Button Long press")
                if button.is_pressed:
                    button.wait_for_release(timeout=None)
            else:
                self._main_queue.put(skibase.TASK_BUTTON_PRESS)
                skibase.log_debug("Button Press")


# ----------------------------- Handling ------------------------------------
def butt_start(main_queue):
    butt_obj = Butt(main_queue)
    butt_obj.start()
    return butt_obj

    
def butt_stop(butt_obj):
    # If still alive; stop
    if butt_obj.status():
        butt_obj.stop()
        butt_obj.join()


# ============================= argparse ====================================
def args_add_butt(parser):
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
    butt_obj = butt_start(main_queue)
    
    # Loop
    skibase.log_notice("Running butt unittest")
    while not skibase.signal_counter and butt_obj.status():
        try:
            task = main_queue.get(block=True, timeout=0.25)
        except queue.Empty:
            task = None
        if task is not None:
            if task == skibase.TASK_BUTTON_PRESS:
                skibase.log_notice("butt press")
            elif task == skibase.TASK_BUTTON_LONG:
                skibase.log_notice("butt long press")
            else:
                skibase.log_warning("butt got unknown task")
        
    # Stop Butt
    butt_stop(butt_obj)

    skibase.log_notice("butt unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

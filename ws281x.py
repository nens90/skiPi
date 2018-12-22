#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal

import skibase

import board
import neopixel



# ============================= NeoPixel ====================================
LED_PIN_DEFAULT = board.D12
LED_COLOR_DEFAULT = "white"
LED_ORDER_DEFAULT = neopixel.GRB
LED_NUM_PIXELS = 100
LED_BRIGHTNESS = 0.2

WS281X_UPDATE_RATE_MS = 30

class Ws281x(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program, default_color):
        super().__init__("WS281x")
        self.program = start_program
        self.default_color = default_color
        
    # --- Loop ---
    def run(self):
        pixels = neopixel.NeoPixel(LED_PIN_DEFAULT,
                                   LED_NUM_PIXELS,
                                   brightness=LED_BRIGHTNESS, 
                                   auto_write=False,
                                   pixel_order=LED_ORDER_DEFAULT)
        while not self._got_stop_event():
            last_program = self.program
            if last_program == 0x00:
                color = (255, 0, 0)
            elif last_program == 0x01:
                color = (0, 255, 0)
            elif last_program == 0x02:
                color = (0, 0, 255)
            elif last_program == 0x03:
                color = (255, 255, 0)
            else:
                color = (255, 255, 255)
            skibase.log_info("program: %02x" %last_program)
            pixels.fill(color)
            while self.program == last_program and not self._got_stop_event():
                pixels.show()
                time.sleep(WS281X_UPDATE_RATE_MS / 1000)


# ----------------------------- Handling ------------------------------------
def ws281x_start(start_program, default_color):
    ws281x_obj = Ws281x(start_program, default_color)
    ws281x_obj.start()
    return ws281x_obj

    
def ws281x_stop(ws281x_obj):
    # If still alive; stop
    if ws281x_obj.status():
        ws281x_obj.stop()
        ws281x_obj.join()


# ============================= argparse ====================================
def args_add_ws281x(parser):
    # ledpin
    parser.add_argument(
      '-l', '--pin',
      type=int,
      action="store",
      dest="ledpin",
      default=LED_PIN_DEFAULT,
      help="Pin number that the data pin of the LED strip is connected to."
    )
    # ledtype
    
    # default color
    parser.add_argument(
      '-c', '--color',
      type=str,
      action="store",
      dest="color",
      default=LED_COLOR_DEFAULT,
      help="Default color of WS281x. (Default: %s)" %LED_COLOR_DEFAULT
    )
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_ws281x(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # ws281x
    program = 0
    ws281x_obj = ws281x_start(program, args.color)
    
    # Loop
    skibase.log_notice("Running WS281x unittest")
    counter = 0
    while not skibase.signal_counter and ws281x_obj.status():
        ws281x_obj.program = counter%4
        time.sleep(5)
        counter += 1

    ws281x_obj = ws281x_stop(ws281x_obj)
    skibase.log_notice("WS281x unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

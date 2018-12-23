#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal
import random

import skibase

import board
import neopixel



# ============================= NeoPixel ====================================
NEO_PIN_DEFAULT = board.D12
NEO_COLOR_DEFAULT = "random"
NEO_ORDER_DEFAULT = neopixel.GRB
NEO_NUM_PIXELS = 100
NEO_BRIGHTNESS = 0.2

WS281X_UPDATE_RATE_MS = 30

NEO_COLORS = {
    "red"    = (255,   0,   0)
    "green"  = (  0, 255,   0)
    "blue"   = (  0,   0, 255)
    "orange" = (255, 128, 128)
    "purple" = (255,   0, 255)
    "yellow" = (0,   255, 255)
    "white"  = (255, 255, 255)
    "random" = (random.randint(0,255),
                random.randint(0,255),
                random.randint(0,255))
}


class Ws281x(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program, default_color_str):
        super().__init__("WS281x")
        self.program = start_program
        try:
            self.default_color = NEO_COLORS[default_color_str]
        except:
            self.default_color = NEO_COLORS["random"]
        
    # --- Loop ---
    def run(self):
        pixels = neopixel.NeoPixel(NEO_PIN_DEFAULT,
                                   NEO_NUM_PIXELS,
                                   brightness=NEO_BRIGHTNESS, 
                                   auto_write=False,
                                   pixel_order=NEO_ORDER_DEFAULT)
        while not self._got_stop_event():
            last_program = self.program
            if last_program == 0x00:
                color = self.default_color
            elif last_program == 0x01:
                color = NEO_COLORS["red"]
            elif last_program == 0x02:
                color = NEO_COLORS["green"]
            elif last_program == 0x03:
                color = NEO_COLORS["blue"]
            else:
                color = NEO_COLORS["random"]
            skibase.log_info("ws281x: %02x" %last_program)
            pixels.fill(color)
            while self.program == last_program and not self._got_stop_event():
                pixels.show()
                time.sleep(WS281X_UPDATE_RATE_MS / 1000)
        pixels.fill((0, 0, 0)) # not stop fill with no color
        


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
      default=NEO_PIN_DEFAULT,
      help="Pin number that the data pin of the LED strip is connected to."
    )
    # ledtype
    
    # default color
    parser.add_argument(
      '-c', '--color',
      type=str,
      action="store",
      dest="color",
      default=NEO_COLOR_DEFAULT,
      help="Default color of WS281x. (Default: %s)" %NEO_COLOR_DEFAULT
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

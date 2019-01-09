#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal
import random

import board
import neopixel

import skibase

    
# ============================= NeoPixel ====================================
NEO_PIN_DEFAULT = board.D12
NEO_COLOR_DEFAULT = "random"
NEO_ORDER_DEFAULT = neopixel.GRB
NEO_NUM_PIXELS = 100
NEO_BRIGHTNESS = 0.2

WS281X_UPDATE_RATE_MS = 30

NEO_COLORS = { #  R    B    G
    "none"   : (  0,   0,   0),
    "red"    : (255,   0,   0),
    "blue"   : (  0, 255,   0),
    "green"  : (  0,   0, 255),
    "orange" : (219,   0,  36),
    "purple" : (129, 126,   0),
    "pink"   : (198,  57,   0),
    "yellow" : (174,   0,  81),
    "cyan"   : (0,   102, 153),
    "white"  : (127, 127, 127),
    "random" : (random.randint(0,127),
                random.randint(0,127),
                random.randint(0,127))
}


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, b, g)


class Ws281x(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program, default_color):
        super().__init__("WS281x")
        self.program = start_program
        if default_color in NEO_COLORS:
            self.default_color = default_color
        else:
            self.default_color = "random"
        

    # --- Loop ---
    def run(self):
        self.pixels = neopixel.NeoPixel(NEO_PIN_DEFAULT,
                                        NEO_NUM_PIXELS,
                                        brightness=NEO_BRIGHTNESS, 
                                        auto_write=False,
                                        pixel_order=NEO_ORDER_DEFAULT)
        while not self._got_stop_event():
            last_program = self.program
            skibase.log_info("ws281x: %02x" %last_program)
            if last_program == 0x00:
                self.fill(self.default_color)
                self.wait_event(last_program, 10)
            elif last_program == 0x01:
                self.fill("red")
                self.wait_event(last_program, 10)
            elif last_program == 0x02:
                self.fill("green")
                self.wait_event(last_program, 10)
            elif last_program == 0x03:
                self.fill("blue")
                self.wait_event(last_program, 10)
            elif last_program == 0x04:
                self.fill("orange")
                self.wait_event(last_program, 10)
            elif last_program == 0x05:
                self.fill("purple")
                self.wait_event(last_program, 10)
            elif last_program == 0x06:
                self.fill("yellow")
                self.wait_event(last_program, 10)
            elif last_program == 0x07:
                self.fill("cyan")
                self.wait_event(last_program, 10)
            elif last_program == 0x08:
                self.rainbow()
                self.wait_event(last_program, 10)
            elif last_program == 0xff:
                self.fill("none")
                self.wait_event(last_program, 10)
            else:
                self.fill("randow")
                self.wait_event(last_program, 10)
        # at stop fill with no color
        self.fill("none")
        
        
    def wait_event(self, program, delay_ms):
        while self.program == program and not self._got_stop_event():
            time.sleep(delay_ms / 1000)
        
    def fill(self, color):
        self.pixels.fill(NEO_COLORS[color])
        self.pixels.show()
        
    def rainbow(self):
        for i in range(NEO_NUM_PIXELS):
            pixel_index = (i * 256 // NEO_NUM_PIXELS)
            self.pixels[i] = wheel(pixel_index & 255)
        self.pixels.show()

        
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
        ws281x_obj.program = counter%9
        time.sleep(3)
        counter += 1

    ws281x_obj = ws281x_stop(ws281x_obj)
    skibase.log_notice("WS281x unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

#!/usr/bin/env python3
"""
TODO
"""

import time
import argparse
import signal
import random
import math

import board
import neopixel

import skibase

    
# ============================= NeoPixel ====================================
NEO_PIN_DEFAULT = board.D12
NEO_COLOR_DEFAULT = "random"
NEO_ORDER_DEFAULT = neopixel.GRB
NEO_NUM_PIXELS = 25
NEO_BRIGHTNESS = 1.0

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
    "white"  : (150, 150, 150),
    "random" : (random.randint(0,127),
                random.randint(0,127),
                random.randint(0,127))
}



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
            self.pixels.fill((0, 0, 0))
            skibase.log_info("ws281x: %02x" %last_program)
            if last_program == 0x00:
                self.sparkle(last_program, *tuple(int(ti/4) for ti in NEO_COLORS[self.default_color]), 0.010, 2.0)
            elif last_program == 0x01:
                self.snow_sparkle(last_program, 0.010, 2.0)
            elif last_program == 0x02:
                self.color_wipe(last_program, *NEO_COLORS[self.default_color], 0.030)
            elif last_program == 0x03:
                self.twinkle_random(last_program, 0.030)
            elif last_program == 0x04:
                self.strobe(last_program, 255, 255, 255, 0.050)
            elif last_program == 0x05:
                self.fade_in_out(last_program, *NEO_COLORS[self.default_color], 0.030)
            elif last_program == 0x06:
                self.constant_fill(*NEO_COLORS[self.default_color])
                self.wait_event(last_program, 10)
            elif last_program == 0x07:
                self.meteor_rain(last_program, 
                                 *NEO_COLORS[self.default_color],
                                 10, 64, True, 0.030)
            elif last_program == 0x08:
                self.rainbow_cycle(last_program, 0.001)
            elif last_program == 0x09:
                self.running_lights(last_program, *NEO_COLORS[self.default_color], 0.030)
            elif last_program == 0x0A:
                self.theater_chase(last_program, *NEO_COLORS[self.default_color], 0.030)
            elif last_program == 0x0B:
                self.random_flash(last_program, 255, 255, 255, 0.050)
            elif last_program == 0xff:
                self.pixels.show()
                self.wait_event(last_program, 10)
            else:
                self.constant_fill(*NEO_COLORS[self.default_color])
                self.wait_event(last_program, 10)
        # at stop fill with no color
        self.constant_fill(*NEO_COLORS["none"])
        
        
    def wait_event(self, program, delay_ms):
        while self.program == program and not self._got_stop_event():
            time.sleep(delay_ms / 1000)
        
        
    # ------------------------- Programs ------------------------------------
    def constant_fill(self, r, g, b):
        self.pixels.fill((r, g, b))
        self.pixels.show()
        
    def color_wipe(self, this_program,
                   red, green, blue, wait):
        while self.program == this_program and not self._got_stop_event():
            self.pixels.fill((0, 0, 0))
            for i in range(NEO_NUM_PIXELS):
                self.pixels[i] = (red, green, blue)
                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(wait)
                    
    def fade_in_out(self, this_program, 
                    red, green, blue, wait):
        while self.program == this_program and not self._got_stop_event():
            time.sleep(wait)
            
            for k in range(256):
                r = (k/256.0)*red
                g = (k/256.0)*green
                b = (k/256.0)*blue
                self.pixels.fill((int(r), int(g), int(b)))
                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break

            for k in range(255, 0, -2):
                r = (k/256.0)*red
                g = (k/256.0)*green
                b = (k/256.0)*blue
                self.pixels.fill((int(r), int(g), int(b)))
                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break
                
    def strobe(self, this_program,
               red, green, blue,
               flash_time):
        while self.program == this_program and not self._got_stop_event():
            self.pixels.fill((red, green, blue))
            self.pixels.show()
            time.sleep(flash_time/3)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            flash_delay = random.randint(50, 5000)
            time.sleep(flash_time)
                    
    def random_flash(self, this_program,
               red, green, blue,
               flash_time):
        while self.program == this_program and not self._got_stop_event():
            self.pixels.fill((red, green, blue))
            self.pixels.show()
            time.sleep(flash_time)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            flash_delay = random.randint(50, 3000)
            for i in range(int(flash_delay/WS281X_UPDATE_RATE_MS)):
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(WS281X_UPDATE_RATE_MS/1000)
                    
    def twinkle(self, this_program, 
                red, green, blue,
                speedDelay, onlyOne = False):
        while self.program == this_program and not self._got_stop_event():
            pixel = random.randint(0,NEO_NUM_PIXELS-1)
            self.pixels[pixel] = (red, green, blue)
            self.pixels.show()
            time.sleep(speedDelay);
            if onlyOne:
                self.pixels.fill((0, 0, 0))
            if random.randint(0, NEO_NUM_PIXELS+1) >= NEO_NUM_PIXELS:
                self.pixels.fill((0, 0, 0))
                
    def twinkle_random(self, this_program, speedDelay, onlyOne = False):
        def random_color():
            return NEO_COLORS[list(NEO_COLORS)[random.randint(0, len(NEO_COLORS)-1)]]
       
        while self.program == this_program and not self._got_stop_event():
            pixel = random.randint(0,NEO_NUM_PIXELS-1)
            self.pixels[pixel] = random_color()
            self.pixels.show()
            time.sleep(speedDelay);
            if onlyOne:
                self.pixels.fill((0, 0, 0))
            if random.randint(0, NEO_NUM_PIXELS+1) >= NEO_NUM_PIXELS:
                self.pixels.fill((0, 0, 0))
                
    def sparkle(self, this_program,
                red, green, blue, sparkleDelay, speedDelay):
        self.pixels.fill((red, green, blue))
        while self.program == this_program and not self._got_stop_event():
            pixel = random.randint(0, NEO_NUM_PIXELS-1)
            self.pixels[pixel] = (255, 255, 255)
            self.pixels.show()
            time.sleep(sparkleDelay)
            self.pixels[pixel] = (red, green, blue)
            self.pixels.show()
            
            for i in range(int((speedDelay*1000)/WS281X_UPDATE_RATE_MS)):
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(WS281X_UPDATE_RATE_MS/1000)
            
    def snow_sparkle(self, this_program, sparkleDelay, speedDelay):
        self.sparkle(this_program, 20, 20, 20, sparkleDelay, speedDelay)
                    
    def running_lights(self, this_program,
                       red, green, blue, waveDelay):
        while self.program == this_program and not self._got_stop_event():
            position = 0
            for j in range (0, NEO_NUM_PIXELS*2):
                position += 1 # = 0; //Position + Rate;
                for i in range (0, NEO_NUM_PIXELS):
                # sine wave, 3 offset waves make a rainbow!
                # float level = sin(i+Position) * 127 + 128;
                # setPixel(i,level,0,0);
                # float level = sin(i+Position) * 127 + 128;
                    self.pixels[i] = (int(((math.sin(i+position) * 127 + 128)/255)*red),
                                      int(((math.sin(i+position) * 127 + 128)/255)*green),
                                      int(((math.sin(i+position) * 127 + 128)/255)*blue))

                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(waveDelay)
        
    def theater_chase(self, this_program,
                      red, green, blue, speedDelay):
        while self.program == this_program and not self._got_stop_event():
            for q in range (0, 3):
                for i in range (0, NEO_NUM_PIXELS-3, +3):
                    self.pixels[i+q] = (red, green, blue) #turn every third pixel on
                self.pixels.show()

                time.sleep(speedDelay)
         
                for i in range (0, NEO_NUM_PIXELS-3, +3):
                    self.pixels[i+q] = (0, 0, 0) #turn every third pixel off
        
    def rainbow_cycle(self, this_program, wait):
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
    
        while self.program == this_program and not self._got_stop_event():
            for j in range(255):
                for i in range(NEO_NUM_PIXELS):
                    pixel_index = (i * 256 // NEO_NUM_PIXELS) + j
                    self.pixels[i] = wheel(pixel_index & 255)
                    
                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(wait)
        
        
    def meteor_rain(self, this_program, 
                    red, green, blue,
                    meteorSize, meteorTrailDecay, meteorRandomDecay,
                    wait):
        def fade_to_black(r,g,b, fadeValue):
            r = 0 if r <= 10 else int(r-(r*fadeValue/256))
            g = 0 if g <= 10 else int(g-(g*fadeValue/256))
            b = 0 if b <= 10 else int(b-(b*fadeValue/256))
            return (r, g, b)

        while self.program == this_program and not self._got_stop_event():  
            for i in range(NEO_NUM_PIXELS+NEO_NUM_PIXELS):
                # fade brightness all LEDs one step
                for ledNo in range(NEO_NUM_PIXELS):
                    if not meteorRandomDecay or random.randint(1,10)>5:
                        self.pixels[ledNo] = fade_to_black(*self.pixels[ledNo],
                                                           meteorTrailDecay)

                # draw meteor
                for j in range(meteorSize):
                    if (i-j<NEO_NUM_PIXELS) and (i-j>=0):
                        self.pixels[i-j] = (red, green, blue)

                self.pixels.show()
                if self.program != this_program or self._got_stop_event():
                    break
                else:
                    time.sleep(wait)
                    
                    
    

        
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

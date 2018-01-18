# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
#
# Based on strandtest.py from https://github.com/jgarff/rpi_ws281x
import time

from neopixel import *

import signal
import sys
import os

from threading import Event

led_event = Event()

led_mode = 1

def signal_stop_handler(signal, frame):
    led_mode = 0
    led_event.set()

def signal_network_handler(signal, frame):
    with open(LED_MODE_FILE, 'r') as f:
        led_mode = int(f.read())
        f.close()
        led_event.set()


# LED strip configuration:
#    Looks like we have 30 leds/m, but a pixel consists of 3 leds.
#    So with 10 pixels/m and 5 meter LED strip we must have 50 pixels.
LED_COUNT      = 50      # Number of LED pixels. (default was 16)
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_RGB   # Strip type and colour ordering
LED_MODE_FILE  = '/var/led.mode'
PID_FILE       = '/var/skipi.pid'
LED_TIMEOUT    = 31 # seconds



# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        led_event.wait(wait_ms/1000.0)
        if (led_event.is_set()):
            return

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            led_event.wait(wait_ms/1000.0)
            if (led_event.is_set()):
                return
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        led_event.wait(wait_ms/1000.0)
        if (led_event.is_set()):
            return

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        led_event.wait(wait_ms/1000.0)
        if (led_event.is_set()):
            return

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            led_event.wait(wait_ms/1000.0)
            if (led_event.is_set()):
                return
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

# Main program logic follows:
if __name__ == '__main__':
    with open(PID_FILE, 'w') as fd:
        fd.write(str(os.getpid()))
        fd.flush()
        fd.close()

    signal.signal(signal.SIGINT, signal_stop_handler)
    signal.signal(signal.SIGUSR1, signal_network_handler)

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    last_led_mode = led_mode
    timestamp = time.time()
    
    while (led_mode != 0):
        # Check timeout
        if (last_led_mode != led_mode): # led mode changed. Update
            timestamp = time.time()
            last_led_mode = led_mode
        elif ((time.time() - timestamp) > LED_TIMEOUT): # Timeout
            led_mode += 1 # Change mode
            last_led_mode = led_mode
            timestamp = time.time()
        # Find led mode
        if (led_mode == 1):
            colorWipe(strip, Color(255, 0, 0))  # Red wipe
        elif (led_mode == 2):
            colorWipe(strip, Color(0, 255, 0))  # Blue wipe
        elif (led_mode == 3):
            colorWipe(strip, Color(0, 0, 255))  # Green wipe
        elif (led_mode == 4):
            theaterChase(strip, Color(127, 127, 127))  # White theater chase
        elif (led_mode == 5):
            theaterChase(strip, Color(127,   0,   0))  # Red theater chase
        elif (led_mode == 6):
            theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
        elif (led_mode == 7):
            rainbow(strip)
        elif (led_mode == 8):
            rainbowCycle(strip)
        elif (led_mode == 9):
            theaterChaseRainbow(strip)
        elif (led_mode == 99):
            colorWipe(strip, Color(0,0,0))
        else:
            theaterChaseRainbow(strip)
    os.remove(PID_FILE)
    colorWipe(strip, Color(0,0,0))

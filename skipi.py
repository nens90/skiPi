# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
#
# Based on strandtest.py from https://github.com/jgarff/rpi_ws281x
import time

from neopixel import *

import sys
import os
import signal

from threading import Event
from threading import Thread

# Network
import select
import socket


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

LED_TIMEOUT    = 15 # seconds
LED_MODE_MAX   = 10

UDP_PORT       = 5005
MSG_MAX_LEN    = 20


led_mode = 1
led_event = Event()

def signal_handler(signal, frame):
    led_mode = 0


# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        led_event.wait(wait_ms/1000.0)
        if (led_event.is_set()):
            led_event.clear()
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
                led_event.clear()
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
            led_event.clear()
            return

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        led_event.wait(wait_ms/1000.0)
        if (led_event.is_set()):
            led_event.clear()
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
                led_event.clear()
                return
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

                
def led_thread(threadname):
    global led_mode
    global led_event
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
            print "LED - Change to mode: ", led_mode
        elif ((time.time() - timestamp) > LED_TIMEOUT): # Timeout
            led_mode += 1 # Change mode
            if led_mode > LED_MODE_MAX:
                led_mode = 1
            last_led_mode = led_mode
            timestamp = time.time()
            print "LED - Timeout: New mode: ", led_mode
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
        elif (led_mode == 10):
            colorWipe(strip, Color(0,0,0))
        else:
            theaterChaseRainbow(strip)
    colorWipe(strip, Color(0,0,0))
    
    
def nwk_thread(threadname):
    global led_mode
    global led_event
    sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
    sock.setblocking(0)
    print "\nReceiver - Opening port for ", str(sys.argv[1])
    sock.bind((str(sys.argv[1]), UDP_PORT)) # needs access to google dns
    
    while led_mode != 0:
        # Network
        ready = select.select([sock], [], [], 0.010) # Non-blocking / wait 10 ms
        if ready[0]:
            data, addr = sock.recvfrom(MSG_MAX_LEN) # buffer size is 20 bytes
            if data:
                led_mode = int(data)
                led_event.set()
                #print "Data: ", led_mode
                

# Main program logic follows:
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print "PID: ", os.getpid()
    nwk_thread = Thread( target=nwk_thread, args=("Thread-Network", ) )
    led_thread = Thread( target=led_thread, args=("Thread-LED", ) )

    nwk_thread.start()
    time.sleep(0.1)
    led_thread.start()
    
    while led_mode != 0:
        time.sleep(1)
    print "Exiting..."

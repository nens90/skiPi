# Funktioner oversat fra https://www.tweaking4all.com/hardware/arduino/adruino-led-strip-effects/

# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel
import random
import math

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D12

# The number of NeoPixels
num_pixels = 25

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1.0, auto_write=False, pixel_order=ORDER)

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
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)

def rainbow_cycle(wait):
    pixels.fill((0, 0, 0))

    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)


def color_wipe(red, green, blue, wait):
    pixels.fill((0, 0, 0))

    for i in range(num_pixels):
        pixels[i] = (red, green, blue)
        pixels.show()
        time.sleep(wait)

def fade_in_out(red, green, blue):
    pixels.fill((0, 0, 0))

    for k in range(256):
        r = (k/256.0)*red
        g = (k/256.0)*green
        b = (k/256.0)*blue
        pixels.fill((int(r), int(g), int(b)))
        pixels.show()

    for k in range(255, 0, -2):
        r = (k/256.0)*red
        g = (k/256.0)*green
        b = (k/256.0)*blue
        pixels.fill((int(r), int(g), int(b)))
        pixels.show()

def strobe(red, green, blue, strobeCount, flashDelay, endPause):
    pixels.fill((0, 0, 0))

    for j in range (0, strobeCount):
        pixels.fill((red, green, blue))
        pixels.show()
        time.sleep(flashDelay)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(flashDelay)
 
    time.sleep(endPause)

def twinkle(red, green, blue, count, speedDelay, onlyOne):
    pixels.fill((0, 0, 0))

    for i in range(0, count):
        pixels[random.randint(0,num_pixels-1)] = (red, green, blue)
        pixels.show()
        time.sleep(speedDelay);
        if onlyOne:
            pixels.fill((0, 0, 0))
  
    time.sleep(speedDelay)

def twinkle_random(count, speedDelay, onlyOne):
    pixels.fill((0, 0, 0))

    for i in range(0, count):
        pixels[random.randint(0,num_pixels-1)] = (random.randint(1,255), random.randint(1,255), random.randint(1,255))
        pixels.show()
        time.sleep(speedDelay)
        if onlyOne:
            pixels.fill((0, 0, 0))
  
    time.sleep(speedDelay)

def sparkle(red, green, blue, speedDelay):
    pixels.fill((0, 0, 0))

    pixel = random.randint(0, num_pixels-1)
    pixels[pixel] = (red, green, blue)
    pixels.show()
    time.sleep(speedDelay)
    pixels[pixel] = (0, 0, 0)

def snow_sparkle(red, green, blue, sparkleDelay, speedDelay):
    pixels.fill((red, green, blue))

    pixel = random.randint(0, num_pixels-1)
    pixels[pixel] = (255, 255, 255)
    pixels.show()
    time.sleep(sparkleDelay)
    pixels[pixel] = (red, green, blue)
    pixels.show()

    time.sleep(speedDelay)

def running_lights(red, green, blue, waveDelay):
    pixels.fill((0, 0, 0))

    position = 0

    for j in range (0, num_pixels*2):
        position += 1 # = 0; //Position + Rate;
        for i in range (0, num_pixels):
        # sine wave, 3 offset waves make a rainbow!
        # float level = sin(i+Position) * 127 + 128;
        # setPixel(i,level,0,0);
        # float level = sin(i+Position) * 127 + 128;
            pixels[i] = (int(((math.sin(i+position) * 127 + 128)/255)*red),
                         int(((math.sin(i+position) * 127 + 128)/255)*green),
                         int(((math.sin(i+position) * 127 + 128)/255)*blue))

        pixels.show()
        time.sleep(waveDelay)

def theater_chase(red, green, blue, speedDelay):
    pixels.fill((0, 0, 0))

    for j in range(0, 10): #do 10 cycles of chasing
        for q in range (0, 3):
            for i in range (0, num_pixels-3, +3):
                pixels[i+q] = (red, green, blue) #turn every third pixel on
            pixels.show()

            time.sleep(speedDelay)
     
            for i in range (0, num_pixels-3, +3):
                pixels[i+q] = (0, 0, 0) #turn every third pixel off


def fade_to_black(ledNo, fadeValue):
    oldColor = pixels[ledNo]

    r,g,b = oldColor

    r = 0 if r <= 10 else int(r-(r*fadeValue/256))
    g = 0 if g <= 10 else int(g-(g*fadeValue/256))
    b = 0 if b <= 10 else int(b-(b*fadeValue/256))

    pixels[ledNo] = (r, g, b)
def meteor_rain(red, green, blue, meteorSize, meteorTrailDecay, meteorRandomDecay, wait):
    pixels.fill((0, 0, 0))

    for i in range(num_pixels+num_pixels):
        # fade brightness all LEDs one step
        for j in range(num_pixels):
            if not meteorRandomDecay or random.randint(1,10)>5:
                fade_to_black(j, meteorTrailDecay)

        # draw meteor
        for j in range(meteorSize):
            if (i-j<num_pixels) and (i-j>=0):
                pixels[i-j] = (red, green, blue)

        pixels.show()
        time.sleep(wait)

while True:
    #rainbow_cycle(0.001)
    #color_wipe(0, 0, 255, 0.05)
    #fade_in_out(255, 0, 0)
    #strobe(55, 165, 0, 10, 0.05, 1)
    #twinkle(255, 165, 0, 20, 0.1, False)
    #twinkle_random(20, 0.1, False)
    #sparkle(165, 255, 0, 0)
    #snow_sparkle(16, 16, 16, 0.002, 0.5)
    #running_lights(255, 165, 0, 0.05)
    #theater_chase(255, 165, 0, 0.05)
    meteor_rain(255, 165, 0, 10, 64, True, 0.030)

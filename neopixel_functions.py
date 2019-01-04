# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel
import random

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D12

# The number of NeoPixels
num_pixels = 30

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER)

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
        pixels.fill((r, g, b))
        pixels.show()

    for k in range(255, 0, -2):
        r = (k/256.0)*red
        g = (k/256.0)*green
        b = (k/256.0)*blue
        pixels.fill((r, g, b))
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
        pixels[random.randint(1,num_pixels)] = (red, green, blue)
        pixels.show()
        time.sleep(speedDelay);
        if onlyOne:
            pixels.fill((0, 0, 0))
  
    time.sleep(speedDelay)

def twinkle_random(count, speedDelay, onlyOne):
    pixels.fill((0, 0, 0))

    for i in range(0, count):
        pixels[random.randint(1,num_pixels)] = (random.randint(1,255), random.randint(1,255), random.randint(1,255))
        pixels.show()
        time.sleep(speedDelay)
        if onlyOne:
            pixels.fill((0, 0, 0))
  
    time.sleep(speedDelay)

def sparkle(red, green, blue, speedDelay):
    pixels.fill((0, 0, 0))

    pixel = random.randint(1, num_pixels)
    pixels[pixel] = (red, green, blue)
    pixels.show()
    time.sleep(speedDelay)
    pixels[pixel] = (0, 0, 0)

def snow_sparkle(red, green, blue, sparkleDelay, speedDelay):
    pixels.fill((0, 0, 0))

    pixel = random.randint(1, num_pixels)
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
            pixels[i] = (((sin(i+Position) * 127 + 128)/255)*red, ((sin(i+Position) * 127 + 128)/255)*green, ((sin(i+Position) * 127 + 128)/255)*blue)

    pixels.show()
    time.sleep(waveDelay)

def theater_chase(red, green, blue, speedDelay):
    pixels.fill((0, 0, 0))

    for j in range(0, 10): #do 10 cycles of chasing
        for q in range (0, 3):
            for i in range (0, num_pixels, +3):
                pixels[i+q] = (red, green, blue) #turn every third pixel on
            pixels.show()

            time.sleep(speedDelay)
     
            for i in range (0, num_pixels, +3):
                pixels[i+q] = (0, 0, 0) #turn every third pixel off


# FIXME: Nedenstående funktion skal oversættes fra C til python
# def fade_to_black(ledNo, fadeValue):
#     oldColor = pixels[ledNo]
#     r = (oldColor & 0x00ff0000UL) >> 16
#     g = (oldColor & 0x0000ff00UL) >> 8
#     b = (oldColor & 0x000000ffUL)

#     r=(r<=10)? 0 : (int) r-(r*fadeValue/256)
#     g=(g<=10)? 0 : (int) g-(g*fadeValue/256)
#     b=(b<=10)? 0 : (int) b-(b*fadeValue/256)
    
#     pixels[ledNo] = (r, g, b)

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
    rainbow_cycle(0.001)
    color_wipe(255, 165, 0, 0.001)
    fade_in_out(255, 165, 0)
    strobe(255, 165, 0, 10, 50, 1000)
    twinkle(255, 165, 0, 20, 100, false)
    twinkle_random(20, 100, false)
    sparkle(255, 165, 0, 0)
    snow_sparkle(16, 16, 16, 20, 500)
    running_lights(255, 165, 0, 50)
    theater_chase(255, 165, 0, 50)
    #meteor_rain(255, 165, 0, 10, 64, True, 30)
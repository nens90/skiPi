#!/usr/bin/env python3
"""
TODO
"""

import time
import math
import argparse
import signal
import random
import numpy

import scrollphathd

import skibase


HEIGHT = scrollphathd.DISPLAY_HEIGHT
WIDTH = scrollphathd.DISPLAY_WIDTH


# ============================= Helpers =====================================


    
# ============================= Scroll PHAT =================================
SCROLL_TEXT_RATE_MS = 30
BRIGHTNESS = 0.5

class Sphat(skibase.ThreadModule):
    """
    TODO
    """
    
    # === Thread handling ===
    def __init__(self, start_program):
        super().__init__("Sphat")
        self.program = start_program
        
    # --- Loop ---
    def run(self):
        while not self._got_stop_event():
            this_program = self.program
            skibase.log_info("sphat: %02x" %this_program)
            scrollphathd.clear()
            if this_program == 0x00:
                self.do_swirl(this_program)
            elif this_program == 0x01:
                self.do_plasma(this_program)
            elif this_program == 0x02:
                self.do_storm(this_program)
            elif this_program == 0x03:
                self.do_cells(this_program)
            elif this_program == 0x04:
                self.do_forest_fire(this_program)
            elif this_program == 0x05:
                self.do_graph(this_program)
            elif this_program == 0x06:
                self.show_string(this_program, "...!...6")
            elif this_program == 0x07:
                self.show_string(this_program, "...!...7")
            elif this_program == 0x08:
                self.show_string(this_program, "...!...8")
            elif this_program == 0xff:
                pass # do nothing as sphat is cleared
            else:
                scroll_string = "ERROR%d" %this_program

                
    # === Programs ===
    def show_string(self, this_program, text):
        scrollphathd.write_string(text, brightness=BRIGHTNESS)
        while self.program == this_program and not self._got_stop_event():
            scrollphathd.show()
            scrollphathd.scroll()
            time.sleep(SCROLL_TEXT_RATE_MS / 1000)
    
    
    def do_swirl(self, this_program):
        def swirl(x, y, step):
            x -= (scrollphathd.DISPLAY_WIDTH/2.0)
            y -= (scrollphathd.DISPLAY_HEIGHT/2.0)

            dist = math.sqrt(pow(x, 2) + pow(y, 2))

            angle = (step / 10.0) + dist / 1.5

            s = math.sin(angle)
            c = math.cos(angle)

            xs = x * c - y * s
            ys = x * s + y * c

            r = abs(xs + ys)
            return max(0.0, 0.7 - min(1.0, r/8.0))
        
        while self.program == this_program and not self._got_stop_event():
            timestep = math.sin(time.time() / 18) * 1500
            
            for x in range(0, WIDTH):
                for y in range(0, HEIGHT):
                    v = swirl(x, y, timestep)
                    scrollphathd.pixel(x, y, v)

            scrollphathd.show()
            time.sleep(0.001)

            
    def do_plasma(self, this_program):
        i = 0

        while self.program == this_program and not self._got_stop_event():
            i += 2
            s = math.sin(i / 50.0) * 2.0 + 6.0

            for x in range(0, 17):
                for y in range(0, 7):
                    v = 0.3 + (0.3 * math.sin((x * s) + i / 4.0) * math.cos((y * s) + i / 4.0))
                    scrollphathd.pixel(x, y, v)

            scrollphathd.show()
            time.sleep(0.01)

            
    def do_storm(self, this_program):
        def generate_lightning(intensity):
            """Generate a lightning bolt"""
            if random.random() < intensity:
                x = random.randint(0, WIDTH-1)
                
                # generate a random crooked path from top to bottom,
                # making sure to not go off the sides
                for y in range(0, HEIGHT):
                    if y > 1 and y < HEIGHT - 1:
                        branch = random.random()
                        if branch < .3:
                            x -= 1
                            if x <= 0:
                                x = 0
                        elif branch > .6:
                            x += 1
                            if x >= WIDTH-1:
                                x = WIDTH-1

                    # generate a wider flash around the bolt itself
                    wide = [int(x-(WIDTH/2)), int(x+(WIDTH/2))]
                    med = [int(x-(WIDTH/4)), int(x+(WIDTH/4))]
                    small = [x-1, x+1]

                    for val in [wide, med, small]:
                        if val[0] < 0:
                            val[0] = 0
                        if val[1] > WIDTH - 1:
                            val[1] = WIDTH - 1

                    for flash in [[wide, .1], [med, .2], [small, .4]]:
                        scrollphathd.fill(
                            flash[1],
                            x=flash[0][0],
                            y=y,
                            width=flash[0][1]-flash[0][0]+1,
                            height=1
                        )

                    scrollphathd.set_pixel(x, y, brightness=1)

                    scrollphathd.show()
                scrollphathd.clear()


        def new_drop(pixels, values):
            """Generate a new particle at the top of the board"""
            
            # First, get a list of columns that haven't generated
            # a particle recently
            cols = []
            for x in range(0, WIDTH):
                good_col = True
                for y in range(0, int(HEIGHT*values['safe'])):
                    if pixels[x][y] == values['brightness']:
                        good_col = False
                if good_col is True:
                    cols.append(x)

            # Then pick a random value from this list,
            # test a random number against the amount variable,
            # and generate a new particle in that column.
            # Then remove it from the list.
            # Do this as many times as required by the intensity variable
            if len(cols) > 0:
                random.shuffle(cols)
                cols_left = values['intensity']
                while len(cols) > 0 and cols_left > 0:
                    if random.random() <= values['amount']:
                        pixels[cols.pop()][0] = values['brightness'] + values['fade']
                    cols_left -= 1


        def fade_pixels(pixel_array, fade):
            """Fade all the lit particles on the board by the fade variable"""
            for x in range(0, WIDTH):
                for y in range(0, HEIGHT):
                    if pixel_array[x][y] > 0:
                        pixel_array[x][y] -= fade
                        pixel_array[x][y] = round(pixel_array[x][y], 2)
                    if pixel_array[x][y] < 0:
                        pixel_array[x][y] = 0
            return pixel_array


        def update_pixels(pixels, values):
            """Update the board by lighting new pixels as they fall"""
            for x in range(0, WIDTH):
                for y in range(0, HEIGHT-1):
                    if pixels[x][y] == values['brightness']:
                        pixels[x][y+1] = values['brightness'] + values['fade']

            fade_pixels(pixels, values['fade'])

            x = range(WIDTH)
            y = range(HEIGHT)
            [[[scrollphathd.set_pixel(a, b, pixels[a][b])] for a in x] for b in y]

            for a in range(0, len(pixels)):
                for b in range(0, len(pixels[a])):
                    scrollphathd.set_pixel(a, b, pixels[a][b])

            scrollphathd.show()
        pixels = []

        for x in range(WIDTH):
            pixels.append([])
            for y in range(HEIGHT):
                pixels[x].append(0)
                
        values = {
          "amount": .7,
          "brightness": .15,
          "delay": 0,
          "fade": .05,
          "intensity": 1,
          "lightning": .01,
          "safe": .3
        }
                
        while self.program == this_program and not self._got_stop_event():
            if values['lightning'] > 0:
                generate_lightning(values['lightning'])
            new_drop(pixels, values)
            update_pixels(pixels, values)
            time.sleep(values['delay'])
            

    def do_cells(self, this_program):
        rules = [22, 30, 54, 60, 75, 90, 110, 150]
        rule = rules[0]
        maxSteps = 100
        loopCount = 0
        matrix = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.int)
        firstRow = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        matrix[0] = firstRow
        row = 0
        speed = 10

        while self.program == this_program and not self._got_stop_event():
            for y in range(0, HEIGHT):
                for x in range(0, WIDTH):
                    scrollphathd.pixel(x, y, matrix[y, x])

            scrollphathd.show()
            loopCount += 1
            
            if loopCount > maxSteps:
                loopCount = 0
                row = 0
                matrix = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.int)
                matrix[0] = firstRow
                rules = numpy.roll(rules, -1, axis=0)
                rule = rules[0]

            inputRow = matrix[row]
            outputRow = numpy.zeros((WIDTH), dtype=numpy.int)

            for x in range(0, WIDTH):
                a = inputRow[x-1] if x > 0 else inputRow[WIDTH-1]
                b = inputRow[x]
                c = inputRow[x+1] if x < WIDTH-1 else inputRow[0]

                o = 1 << ((a << 2) + (b << 1) + c)

                outputRow[x] = 1 if o&rule else 0

            if row < HEIGHT-1:
                row = row + 1
            else:
                matrix = numpy.roll(matrix, -1, axis=0)
            matrix[row] = outputRow

            time.sleep(0.01 * speed)
            
            
    def do_forest_fire(self, this_program):
        # Initial probability of a grid square having a tree
        initial_trees = 0.55

        # p = probability of tree growing, f = probability of fire
        p = 0.01
        f = 0.001

        # Brightness values for a tree, fire, and blank space
        tree, burning, space = (0.3, 0.9, 0.0)

        # Each square's neighbour coordinates
        hood = ((-1,-1), (-1,0), (-1,1),
                (0,-1),          (0, 1),
                (1,-1),  (1,0),  (1,1))

        # Function to populate the initial forest
        def initialise():
            grid = {(x,y): (tree if random.random()<= initial_trees else space) for x in range(WIDTH) for y in range(HEIGHT)}
            return grid

        # Display the forest, in its current state, on Scroll pHAT HD
        def show_grid(grid):
            scrollphathd.clear()
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    scrollphathd.set_pixel(x, y, grid[(x, y)])
            scrollphathd.show()

        # Go through grid, update grid squares based on state of
        # square and neighbouring squares
        def update_grid(grid):
            new_grid = {}
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    if grid[(x, y)] == burning:
                        new_grid[(x, y)] = space
                    elif grid[(x, y)] == space:
                        new_grid[(x, y)] = tree if random.random() <= p else space
                    elif grid[(x, y)] == tree:
                        new_grid[(x, y)] = (burning if any(grid.get((x + dx, y + dy), space) == burning for dx, dy in hood) or random.random() <= f else tree)
            return new_grid
    
        grid = initialise()
        while self.program == this_program and not self._got_stop_event():
            show_grid(grid)
            grid = update_grid(grid)
            time.sleep(0.05)

            
    def do_graph(self, this_program):
        min_value = 0
        max_value = 50        
        values = [0] * WIDTH

        while self.program == this_program and not self._got_stop_event():
            values.insert(0, random.randrange(min_value, max_value))
            values = values[:WIDTH]
            scrollphathd.set_graph(values,
                                   low=min_value,
                                   high=max_value,
                                   brightness=0.3)
            scrollphathd.show()
            time.sleep(0.03)
        
        
# ----------------------------- Handling ------------------------------------
def sphat_start(start_program):
    sphat_obj = Sphat(start_program)
    sphat_obj.start()
    return sphat_obj

    
def sphat_stop(sphat_obj):
    # If still alive; stop
    if sphat_obj.status():
        sphat_obj.stop()
        sphat_obj.join()

        
# ============================= argparse ====================================
def args_add_sphat(parser):
    return parser



# ============================= Unittest ====================================
def test():
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = skibase.args_add_log(parser)
    parser = args_add_sphat(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # sphat
    program = 0
    sphat_obj = sphat_start(program)
    
    # Loop
    skibase.log_notice("Running Scroll PHAT unittest")
    counter = 0
    while not skibase.signal_counter and sphat_obj.status():
        sphat_obj.program = counter%9
        time.sleep(8)
        counter += 1

    sphat_obj = sphat_stop(sphat_obj)
    skibase.log_notice("Scroll PHAT unittest ended")

    
if __name__ == '__main__':
    test()

#EOF

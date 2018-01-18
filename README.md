**Convert to HTML:**  
Install [pandoc](https://pandoc.org/MANUAL.html) and run:  

    pandoc --toc README.md -o README.html

# skiPi
LED solution for Raspberry Pi ski holiday.

yayay ayyayayy y


## Usefull stuff

* [LED strip on aliexpress](https://www.aliexpress.com/item/WS2811-led-strip-5m-150-Pixels-ws2811-ic-DC-12V-led-strip-Addressable-Digital-5050-RGB/32830405129.html?spm=a2g0s.9042311.0.0.6FlhxP)
* [Some guide](https://learn.adafruit.com/neopixels-on-raspberry-pi?view=all)
* [rpi_ws281x](https://github.com/jgarff/rpi_ws281x)
* [stackexchange about level conversion](https://electronics.stackexchange.com/questions/210205/driving-ws2811-led-strip-from-microcontroller)
* [Datasheet](https://cdn-shop.adafruit.com/datasheets/WS2811.pdf)


## Getting Started  

### Setup ###  

    sudo apt-get update
    sudo apt-get upgrade
    sudo shutdown -r now
    # Set hostname
    sudo raspi-config
    
### Get packages ###  

    sudo apt-get install python3-pip
    sudo apt-get install build-essential python-dev git scons swig
    
### Neopixel lib stuff ###  

    cd ~/
    git clone https://github.com/jgarff/rpi_ws281x.git
    cd rpi_ws281x
    scons
    cd python
    sudo python setup.py install
    # test that neopixel works
    sudo python examples/strandtest.py
    
### skiPi ###  

    cd ~/
    git clone https://github.com/nens90/skiPi.git
    cd skiPi
    # Run the awesome app!
    ./skipi.sh
	
### skiPi Sender ###  

    ./skipi_sender.sh

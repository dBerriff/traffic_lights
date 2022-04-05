#MicroPython on RPi Pico
from machine import Pin
from time import sleep, time
import random

"""Simulates UK traffic light sequence on LEDs
   Tested on:
   - MicroPython running on Cytron Maker Pi Pico board
   - note: on-board button is hard-wired with pull-up resistor"""


class HardwareIn:
    """for button press - crossing request"""
    
    def __init__(self, b_pin):
        """set button pin as input"""
        self.button = Pin(b_pin, Pin.IN, Pin.PULL_UP)
    
    def check_button(self) -> bool:
        """check for button-press
           Cytron RP2040 on-board button:
           returns:normally 1; 0 while press"""
        return self.button.value() == 0


class GpioPins:
    """given GPIO pins, set logical LED pins for output"""
    
    def __init__(self, out_pins):
        led_pins = []
        for i, pin in enumerate(out_pins):
            led_pins.append(Pin(out_pins[i], Pin.OUT))
        self.led_pins = tuple(led_pins)


class Leds:
    """abstract class for setting LEDs
       - inherited by XLeds and TlLeds"""
    
    Pin_settings = {'R':  (1, 0, 0),
                    'G':  (0, 0, 1),
                    'A':  (0, 1, 0),
                    'RA': (1, 1, 0),
                    'W': (1, 0),
                    'C': (0, 1),
                    'N': (0, 0)}
    
    def __init__(self, led_pins):
        self.led_pins = led_pins
    
    def set_lights(self, state):
        """pins set by [state] lookup"""
        pin_state = self.Pin_settings[state]
        for i, setting in enumerate(pin_state):
            self.led_pins[i].value(setting)
        return pin_state


class XLeds(Leds):
    """red and green crossing lights
       Wait: red; Cross: green; None: for blink"""
    
    def __init__(self, led_pins):
        # super() is the Leds class
        super().__init__(led_pins)
    

class TlLeds(Leds):
    """red, amber and green traffic lights"""
    
    def __init__(self, led_pins):
        # super() is the Leds class
        super().__init__(led_pins)
    

class CrossingLight:
    """simulates simple red/green crossing lights
       - common to all traffic lights"""
    
    def __init__(self, hardware):
        self.hardware = hardware
        self.lights = hardware.set_lights('W')
    
    def __str__(self):
        """for print()"""
        return f'status RG: {self.lights}'

    def set_cross(self):
        """set green Cross light"""
        self.lights = self.hardware.set_lights('C')
        print(f'Cross: {self}')
        sleep(8.0)
    
    def set_flashing(self):
        """set Cross light flashing"""
        t = 0
        print(f'Flash')
        while t < 6:
            self.lights = self.hardware.set_lights('N')
            sleep(1.0)
            self.lights = self.hardware.set_lights('C')
            sleep(1.0)
            t += 2
        self.lights = self.hardware.set_lights('N')
        sleep(1.0)
            
    def set_wait(self):
        """set red Wait light"""
        self.lights = self.hardware.set_lights('W')
        print(f'Wait  : {self}') #===
                
        
class TrafficLight:
    """Simulates multi-way UK traffic lights:
       - RAG signifies: Red, Amber, Green
       - [flags] and [end_hold] control loop actions 
         to allow additional processing except during
         crossing cycle"""

    # Index used to set next Green
    Index = 0
    Go_seq = ('RA', 'G')
    Stop_seq = ('A', 'R')
    # sequence intermediate intervals in seconds;
    # see: https://www.legislation.gov.uk/uksi/
    #      2016/362/schedule/14/made/data.xht
    Pause_RA = 2.5
    Pause_A = 3.0
    
    def __init__(self, hardware):
        self.hardware = hardware
        self.index = TrafficLight.Index
        TrafficLight.Index += 1
        # initialise to Red
        self.lights = hardware.set_lights('R')
        self.green_hold = 0
        self.flashing = False
    
    def __str__(self):
        """for print()"""
        return f'index: {self.index}, status RAG: {self.lights}'

    def set_go(self):
        """stop-to-go sequence"""
        sleep(1.0)
        for state in self.Go_seq:
            self.lights = self.hardware.set_lights(state)
            if state == 'RA':
                sleep(self.Pause_RA)
        # random hold ~ 10s
        self.green_hold = time() + random.randint(8, 12)
        print(f'Go  : {self}') #===
    
    def set_stop(self):
        """go-to-stop sequence"""
        for state in self.Stop_seq:
            self.lights = self.hardware.set_lights(state)
            if state == 'A':
                sleep(self.Pause_A)
        print(f'Stop: {self}') #===
    
    def is_hold_end(self) -> bool:
        """is hold-time ended"""
        return time() > self.green_hold

def cycle(counter, modulus) -> int:
    """cycle counter with modulo division"""
    return (counter + 1) % modulus

def main():
    # instantiate traffic light objects;
    # - parameter: tuple of GPIO pins
    # TrafficLight objects are initialised at Stop
    # TrafficLight[0] is set to Go to start the sequence
    # Crossing sequence initiated when button-press detected
    # then loop indefinitely
    
    print('Initialising:', end='')

    t_lts = (TrafficLight(TlLeds(GpioPins((2, 1, 0)).led_pins)),
             TrafficLight(TlLeds(GpioPins((5, 4, 3)).led_pins)),
             TrafficLight(TlLeds(GpioPins((8, 7, 6)).led_pins))
            )
    n_ways = len(t_lts)
    x_lts = CrossingLight(XLeds(GpioPins((15, 14)).led_pins))
    print(f' {n_ways}-way traffic & single crossing lights')
    # select first green light
    tl_green = t_lts[0]
    #crossing button: GPIO pin
    button = HardwareIn(20)
    
    # set control flags
    can_set_green = False
    set_crossing = False
    
    # start the sequence
    x_lts.set_wait()
    tl_green.set_go()

    # loop indefinitely
    while True:
        if tl_green.is_hold_end():
            tl_green.set_stop()
            # set flag: next-green pending and allow-crossing
            can_set_green = True
        
        if button.check_button():
            set_crossing = True
        
        if set_crossing:
            # crossing requested
            if can_set_green:
                # all lights Red so cross...
                x_lts.set_cross()
                x_lts.set_flashing() #flash green
                x_lts.set_wait()
                set_crossing = False
            else:
                # for testing, overwrite on loop
                print('WAIT', end='\r')
            
        if can_set_green:
            # set next green in sequence to Go
            tl_green = t_lts[cycle(tl_green.index, n_ways)]
            tl_green.set_go()
            can_set_green = False
            
        # do something else...
        # check for crossing button on each loop
        sleep(0.1)

if __name__ == '__main__':
    main()
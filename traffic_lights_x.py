from machine import Pin
from time import sleep, time
import random

""" Simulates UK traffic light sequence on LEDs
    - MicroPython on RP2040 board
    - Classes broken out for clarity and cohesion
    - TODO: investigate functional design alternative"""


class ButtonIn:
    """button press - used for ped-X request"""
    
    def __init__(self, b_pin):
        """set button pin as input"""
        self.button = Pin(b_pin, Pin.IN)
    
    def check_button(self) -> bool:
        """check for button-press:
           0 for Cytron Nano RP2040 board"""
        return self.button.value() == 0


class TlPins:
    """set GPIO pins for output; return as tuple"""
    
    def __init__(self, out_pins):
        led_pins = []
        for i, pin in enumerate(out_pins):
            led_pins.append(Pin(out_pins[i], Pin.OUT))
        self.led_pins = tuple(led_pins)


class TlLeds:
    """set simulation LED states"""
    
    State_dict = {'R':  (1, 0, 0),
                  'G':  (0, 0, 1),
                  'A':  (0, 1, 0),
                  'RA': (1, 1, 0)}
    
    def __init__(self, led_pins):
        self.led_pins = led_pins
    
    def set_lights(self, state) -> tuple:
        """pins set by [state] lookup"""
        pin_state = self.State_dict[state]
        for i, setting in enumerate(pin_state):
            self.led_pins[i].value(setting)
        return pin_state
    

class TrafficLight:
    """Simulates UK traffic light sequence:
       - RAG signifies: Red, Amber, Green
       - flags and end_hold: control loop actions 
         to allow additional processing
       - threading considered but still in
         development for MicroPython"""

    # track instantiations
    Index = 0
    Go_seq = ('RA', 'G')
    Stop_seq = ('A', 'R')
    # sequence intermediate intervals in seconds
    # see: https://www.legislation.gov.uk/uksi/
    #      2016/362/schedule/14/made/data.xht
    Pause_RA = 2.0
    Pause_A = 3.0
    
    def __init__(self, red, amber, green):
        self.hardware = TlLeds(TlPins((red, amber, green)).led_pins)
        self.index = TrafficLight.Index
        TrafficLight.Index += 1
        self.lights = self.hardware.set_lights('R')
        self.green_hold = 0
    
    def __str__(self):
        return f'index: {self.index} RAG: {self.lights}'

    def set_go(self):
        """stop_to_go sequence"""
        for state in self.Go_seq:
            self.lights = self.hardware.set_lights(state)
            if state == 'RA': sleep(self.Pause_RA)
        # random hold ~ 10s
        self.green_hold = time() + random.randint(8, 12)
        print(f'Go  : {self}')
    
    def set_stop(self):
        """go-to-stop sequence"""
        for state in self.Stop_seq:
            self.lights = self.hardware.set_lights(state)
            if state == 'A': sleep(self.Pause_A)
        print(f'Stop: {self}')
    
    def is_hold_end(self):
        """is hold-time ended?"""
        return time() > self.green_hold
        
def increment(counter, modulus):
    """cycle counter with modulo division"""
    return (counter + 1) % modulus

def main():
    # instantiate traffic light objects as a tuple
    # (R, A, G) GPIO pins specified for each light
    # TrafficLight objects are initialised at Stop
    # TrafficLight[0] is set to Go to start the sequence
    print('Initialising...')
    tls = (
           TrafficLight(2, 1, 0),
           TrafficLight(6, 5, 4)
          )
    n_ways = len(tls)
    # select first green light
    tl_green = tls[0]
    #instantiate crossing button -> GPIO pin
    button = ButtonIn(20)
    
    # set control flags
    set_green = False
    set_cross = False
    
    # start the sequence
    tl_green.set_go()

    # loop continuously
    while True:
        if tl_green.is_hold_end():
            tl_green.set_stop()
            # set flag: next-green and allow-crossing
            set_green = True
        
        if button.check_button():
            set_cross = True
        
        if set_cross:
            if set_green:
                print('crossing in progress...')
                sleep(5.0)
                print('crossing completed')
                set_cross = False
            else:
                print('WAIT', end='\r')
            
        if set_green:
            # set next green light in sequence
            tl_green = tls[increment(tl_green.index, n_ways)]
            tl_green.set_go()
            set_green = False
            
        # do something else...
        sleep(0.1)

if __name__ == '__main__':
    main()
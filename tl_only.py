#MicroPython
from machine import Pin
from time import sleep, time
from random import randint

"""Simulates UK traffic light sequence on LEDs
   Tested: MicroPython v1.18 on RPi Pico"""


class GpioPins:
    """given GPIO out_pins:
       - set logical led_pins for output"""
    
    def __init__(self, out_pins):
        led_pins = []
        for i, pin in enumerate(out_pins):
            led_pins.append(Pin(out_pins[i], Pin.OUT))
        self.led_pins = tuple(led_pins)


class TlLeds:
    """set LEDs """
    
    # settings dictionary: 'state' is key
    Pin_settings = {'R': (1, 0, 0),
                    'G': (0, 0, 1),
                    'A': (0, 1, 0),
                    'RA': (1, 1, 0)}
    
    def __init__(self, led_pins):
        self.led_pins = led_pins
    
    def set_lights(self, state):
        """light state -> pin_state"""
        pin_state = self.Pin_settings[state]
        for i, setting in enumerate(pin_state):
            self.led_pins[i].value(setting)
        return pin_state # for print()


class TrafficLight:
    """Simulates multi-way UK traffic lights.
       https://www.legislation.gov.uk/uksi/
       2016/362/schedule/14/made/data.xht"""

    # Index tracks object set to green
    Index = 0
    Change_seq = {'GO': ('RA', 'G'),
                  'ST': ('A', 'R')}
    # 
    Pause_RA = 2.5 # s
    Pause_A = 3.0 # s
    Pause_switch = 0.2 # s
    
    def __init__(self, hardware):
        self.hardware = hardware
        self.index = TrafficLight.Index
        TrafficLight.Index += 1
        self.lights = hardware.set_lights('R')
        self.green_hold = 0
    
    def __str__(self):
        """for print()"""
        return f'tl index: {self.index}, RAG: {self.lights}'

    def set_state(self, state_change):
        for state in self.Change_seq[state_change]:
            self.lights = self.hardware.set_lights(state)
            print(f'Change: {self}')
            if state == 'RA':
                sleep(self.Pause_RA)
            elif state == 'A':
                sleep(self.Pause_A)
            else:
                # instant switching can look unrealistic
                sleep(self.Pause_switch)
    
    def set_go(self):
        """set to Go and store end time"""
        self.set_state('GO')
        # set hold time ~ 10s
        self.green_hold = time() + randint(8, 12) # s
    
    def set_stop(self):
        """set to Stop"""
        self.set_state('ST')
        
    def hold_is_over(self):
        return time() > self.green_hold
        
    
def main():
    # Instantiate traffic light objects; initialised at Stop
    # TrafficLight[0] is set to Go to start the sequence
    
    print('Initialising:', end='')

    t_lts = (
             TrafficLight(TlLeds(GpioPins((2, 1, 0)).led_pins)),
             TrafficLight(TlLeds(GpioPins((5, 4, 3)).led_pins)),
             TrafficLight(TlLeds(GpioPins((8, 7, 6)).led_pins))
            )
    
    n_ways = len(t_lts)
    print(f' {n_ways}-way traffic lights')
    # select first green light
    tl_green = t_lts[0]
    tl_green.set_go()

    def get_next(index) -> int:
        """cycle index, modulo n_ways"""
        return (index + 1) % n_ways

    # loop indefinitely
    while True:
        if tl_green.hold_is_over():
            tl_green.set_stop()
            # change to next green by index
            tl_green = t_lts[get_next(tl_green.index)]
            tl_green.set_go()            
        # do something else...
        sleep(0.1)

if __name__ == '__main__':
    main()
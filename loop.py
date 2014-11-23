#!/usr/bin/python

import os
import os.path
import sys
import select
import time
import optparse

import RPi.GPIO

import log

class Loop():
    def __init__(self, d0):
        self.d0 = d0
        self.fd = None
        self.state = None

    def setup_input(self):
        chan = self.d0
        gpio_d = '/sys/class/gpio/gpio%d' % chan
        if os.path.exists(gpio_d):
            open('/sys/class/gpio/unexport','wb').write('%d\n' % chan)
        open('/sys/class/gpio/export','wb').write('%d\n' % chan)
        RPi.GPIO.setmode(RPi.GPIO.BCM);
        RPi.GPIO.setup(chan, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
        open(os.path.join(gpio_d, 'edge'), 'wb').write('both\n')
        self.fd = os.open(os.path.join(gpio_d, 'value'), os.O_RDONLY)

    def read(self):
        os.lseek(self.fd,0,0)
        value =  os.read(self.fd,1)
        self.state = int(value)
        return self.state

    def check_loop(self, timeout = 0.1):
        (i, o, x) = select.select([], [], [self.fd, ], timeout)
        if x:
            old_state = self.state
            new_state = self.read()
            if new_state != old_state:
                return new_state
        return None

   
    
def main():

    usage = """%prog --data-dir PATH --gpio N --name NAME"""
    parser = optparse.OptionParser(usage)
    parser.add_option("--gpio", dest="gpio",
                      action="store", type="int", help="gpio pin loop is on")
    parser.add_option("--name", dest="name",
                      action="store", help="loop name ex: front_gate_loop")
    parser.add_option("--data-dir", dest="data_dir",
                      action="store", help="path to log directory")

    (options, args) = parser.parse_args()
    
    data_dir = options.data_dir
    name = options.name
    gpio = options.gpio
    
    if not (data_dir and name and gpio):
        parser.print_help()
        exit(2)

    l = Loop(d0=int(gpio))
    l.setup_input()
    while True:
        v = l.check_loop()
        if v != None:
            if v == 0:
                e = {'event':'loop_closed'}
            else:
                e = {'event':'loop_open'}
            
            #print 'got:', v, e
            log.log(name, e, data_dir)

if __name__ == '__main__':
    main()

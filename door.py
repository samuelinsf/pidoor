#!/usr/bin/python

import os
import os.path
import sys
import select
import optparse

import RPi.GPIO
import lazytable
import log


class Door():
    def __init__(self, d0, d1, relay):
        self.d0 = d0
        self.d1 = d1
        self.relay = relay
        self.fd={}
        self.relock_after = self._get_time()

    def _setup_input(self, chan, data_bit):
        gpio_d = '/sys/class/gpio/gpio%d' % chan
        if os.path.exists(gpio_d):
            open('/sys/class/gpio/unexport','wb').write('%d\n' % chan)
        open('/sys/class/gpio/export','wb').write('%d\n' % chan)
        RPi.GPIO.setmode(RPi.GPIO.BCM);
        RPi.GPIO.setup(chan, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
        #open(os.path.join(gpio_d, 'edge'), 'wb').write('falling\n')
        open(os.path.join(gpio_d, 'edge'), 'wb').write('falling\n')
        fd = os.open(os.path.join(gpio_d, 'value'), os.O_RDONLY)
        #print 'fd', chan, fd, os.read(fd, 1)
        self.fd[fd] = (self, data_bit)
        
    def _get_time(self):
        # we use the system uptime because the wall
        # time may jump around in the embeded system
        return float(open('/proc/uptime').read().split()[0])

    def setup_inputs(self):
        self._setup_input(self.d0, 0)
        self._setup_input(self.d1, 1)

    def setup_output(self):
        gpio_d = '/sys/class/gpio/gpio%d' % self.relay
        if os.path.exists(gpio_d):
            open('/sys/class/gpio/unexport','wb').write('%d\n' % self.relay)
        open('/sys/class/gpio/export','wb').write('%d\n' % self.relay)
        open(os.path.join(gpio_d, 'direction'), 'wb').write('low\n')

    def read_card(self):
        bitsread = 0
        value = 0
        timeout = .1
        #print  'fd keys', self.fd.keys()
        for fd in  self.fd.keys():
            os.lseek(fd,0,0)
            os.read(fd,1)
        (i, o, x) = select.select([], [], self.fd.keys(), timeout)
        while bitsread < 26:
            #print x
            if not x:
                # timeout
                break
            if len(x) > 1:
                # error
                print 'error'
                break
            value = (value << 1) + self.fd[x[0]][1]
            os.lseek(x[0],0,0)
            os.read(x[0],1)
            bitsread += 1
            (i, o, x) = select.select([], [], self.fd.keys(), timeout)
            #print bitsread, value
        value = value >> 1
        value = value & 0xffffff
        return value

    def open_door(self, seconds):
        gpio_d = '/sys/class/gpio/gpio%d' % self.relay
        self.relock_after = self._get_time() + seconds
        open(os.path.join(gpio_d, 'value'), 'wb').write('1\n')
        
    def maintain_door(self):
        max_open_seconds = 6
        gpio_d = '/sys/class/gpio/gpio%d' % self.relay
        now = self._get_time()
        if now > self.relock_after:
            open(os.path.join(gpio_d, 'value'), 'wb').write('0\n')

        if (self.relock_after - now ) > max_open_seconds:
            # timer wrap?
            # somehow its too far out in future to close door
            # just close door
            open(os.path.join(gpio_d, 'value'), 'wb').write('0\n')

def card_allowed(card, door, path):
    card_db = os.path.join(path, 'cards_db.sqlite')
    t = lazytable.open(card_db, 'cards')
    r = list(t.get({'card': card, 'door': door}))
    disposition = 'card_not_known'
    is_allowed = 0
    note = ''
    if r:
        is_allowed = r[0]['is_allowed']
        disposition = 'card_known'
        note = r[0]['note']

    log.log(door,
            {'is_allowed': is_allowed, 
            'disposition': disposition, 
            'card': card, 
            'door':door,
            'card_note':note
            }, path)
    return (is_allowed == 1)
            
def main():
    usage = """%prog --data-dir PATH --d0 N --d1 N --relay N --name NAME"""
    parser = optparse.OptionParser(usage)
    parser.add_option("--d0", dest="d0",
                      action="store", type="int", help="gpio pin for weigand d0")
    parser.add_option("--d1", dest="d1",
                      action="store", type="int", help="gpio pin for weigand d1")
    parser.add_option("--relay", dest="relay",
                      action="store", type="int", help="gpio pin for latch buzzer relay")
    parser.add_option("--name", dest="name",
                      action="store", help="door name ex: front_gate")
    parser.add_option("--data-dir", dest="data_dir",
                      action="store", help="path to dir with logs and carddb")

    (options, args) = parser.parse_args()

    data_dir = options.data_dir
    name = options.name
    d0 = options.d0
    d1 = options.d1
    relay = options.relay

    if not (data_dir and name and d0 and d1 and relay):
        parser.print_help()
        exit(2)

    d = Door(d0=d0, d1=d1, relay=relay)
    d.setup_output()
    d.setup_inputs()
    while True:
        v =  d.read_card()
        if v:
            #print 'got:', v
            if card_allowed(v, name, data_dir):
                d.open_door(1)
        d.maintain_door()

if __name__ == '__main__':
    main()

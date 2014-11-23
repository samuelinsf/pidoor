Hardware
--------------
The circuit for the cardreader interface is used twice.
The isolated pulldown to ground scheme also works to
control the cardreader's led and buzzer,
but I didn't need those, and so have left them out.

There is one of the loop isolation circuits for each
of the classic style burglar alarm DC loops I have tracked.
The current installation has 5 of them running.

The LED in the relay control circuit is a backemf quench.
Any diode will do.


Some key parts
------------
The PS2502-4-A is 4 pack of optocouplers.
It is nice because it works great with the Pi's 3.3v gpio,
with the 5v TTL of the Weigand card reader, and can drive the 12v relays.
[http://www.mouser.com/ProductDetail/CEL/PS2502-4-A/?qs=ZyqMiHkgYmNQKZ3ZxC9WTg%3D%3D](http://www.mouser.com/ProductDetail/CEL/PS2502-4-A/?qs=ZyqMiHkgYmNQKZ3ZxC9WTg%3D%3D)

For the magnetic switch, I used:
[http://www.adafruit.com/products/375?gclid=CITIyu2Wj8ICFVJgfgodyTIA6w](http://www.adafruit.com/products/375?gclid=CITIyu2Wj8ICFVJgfgodyTIA6w)

For the card reader I used this nifty low cost 125khz rfid weigand26 reader:
[http://www.dx.com/p/mini-door-access-card-reader-black-116855#.VHEE7ofJ-2w](http://www.dx.com/p/mini-door-access-card-reader-black-116855#.VHEE7ofJ-2w)
Interestingly, my 2003 Honda cardkey also scans with this system.

For keyfobs I use these:
[http://www.dx.com/p/mjid-1-entrance-guard-inductive-id-key-card-blue-10-pcs-224560#.VHEFJofJ-2w](http://www.dx.com/p/mjid-1-entrance-guard-inductive-id-key-card-blue-10-pcs-224560#.VHEFJofJ-2w)

For the solenoid control relay I used:
[http://www.dx.com/p/mini-5-pin-10a-power-relay-for-security-system-black-5-pack-129859#.VHEGJIfJ-2w](http://www.dx.com/p/mini-5-pin-10a-power-relay-for-security-system-black-5-pack-129859#.VHEGJIfJ-2w)

To make everything nice I put all the parts in an alarm system box:
[http://www.amazon.com/Interlogix-NetworX-X-Pand-A-Can-Enclosure-NX-003/dp/B00171A43Y](http://www.amazon.com/Interlogix-NetworX-X-Pand-A-Can-Enclosure-NX-003/dp/B00171A43Y)

To make it robust I soldered everything down onto one of these (with a temperature controlled weller):
(http://www.adafruit.com/products/1135)[http://www.adafruit.com/products/1135]

Because I live in San Francisco my house already had an
entry gate with built in latch solenoid.

For the raspberry Pi I used a model B.

For storing the logs and access database I use a USB thumb drive
mounted in sync mode... I switched to this model after the random
one I was using began to get slow:
(http://www.amazon.com/gp/product/B00KT7DXIU)[http://www.amazon.com/gp/product/B00KT7DXIU]


Setting up the raspberry pi:
I used a raspbian from 2013 for the build.
(http://www.raspbian.org/)[http://www.raspbian.org/] Newer versions will probably work fine.

For robustness I made it readonly root and gave it a static IP.
(https://wiki.debian.org/ReadonlyRoot)[https://wiki.debian.org/ReadonlyRoot]

Installation                                                                                                                                                             
---------------                                                                                                                                                          
Build and connect some hardware (see hardware/)                                                                                                                        

Software side
-------------------
Install lazytable

    pip install lazytable

Copy this repo to /root on the pi.
Add a readwrite mount /data I put it on a thumb drive formatted like so:

    mkfs.ext4 -L DATA /dev/sda1 

With it like this in /etc/fstab:

    LABEL="DATA" /data              ext4    defaults,noatime,sync,nofail  0       2

Install daemontools:

    apt-get install daemontools daemontools-run                                                                                                                          

Make /etc/service a link to /data/service

    mv /etc/service /etc/service.dist
    ln -s /data/service /etc/service

Here is an example service file for door.py:

    mkdir -p /data/service/front_gate 
    cat > /data/service/front_gate/run <<EOF
    #!/bin/bash  
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin 
    cd /root                                                                                                                                                             
    exec 2>&1                                                                                                                                                            
    exec ./door.py --data-dir /data --name front_gate --d0 17 --d1 18 --relay 4
    EOF

door.py uses an access card database which you can edit using card.py

For example, to setup a card with number 1234567:

    ./card.py 1234567 front_gate 1 sam

To see a list of cards and status, run card with no arguments.

    ./card.py


loop.py monitors a DC loop attached to a gpio:

    mkdir -p /data/service/hall_door_loop
    cat > /data/service/hall_door_loop/run <<EOF
    #!/bin/bash
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

    cd /root
    exec 2>&1
    exec ./loop.py --data-dir /data --name hall_door_loop --gpio 24
    EOF

web_ui.py needs some additional configuration, see the
beginning of web_ui.py for an example ini

    mkdir -p /data/service/web_ui
    cat > /data/service/web_ui/run <<EOF
    #!/bin/bash
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

    cd /root
    exec > /dev/null
    exec 2>&1
    exec ./web_ui.py /data/web_ui.ini
    EOF

For robustness I made the Pi readonly root and gave it a static IP.
[https://wiki.debian.org/ReadonlyRoot](https://wiki.debian.org/ReadonlyRoot)

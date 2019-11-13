#!/usr/bin/env python

import sys
import usb
import errno
import array

from greatfet import GreatFET

FREQUENCY    = 1000
READ_LENGTH  = 2

BUFFER_SIZE  = 4096
TIMEOUT      = 10


gf = GreatFET()


endpoint = gf.apis.adc.stream_periodic_read(FREQUENCY)
gf.comms.get_exclusive_access()

buffer = array.array('B', bytes(BUFFER_SIZE))


print("Using endpoint: {}".format(endpoint))
print("")

try:
    while True:

        # Capture data from the device, and unpack it.
        try:
            samples = gf.comms.device.read(endpoint, buffer, TIMEOUT)
            sys.stdout.buffer.write(buffer[0:samples])
            sys.stdout.buffer.flush()


        except usb.core.USBError as e:
            if e.errno != errno.ETIMEDOUT:
                raise

finally:
    gf.apis.adc.stop_periodic_read()
    gf.comms.release_exclusive_access()


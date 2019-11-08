#!/usr/bin/env python

import sys
import usb
import errno
import array

from greatfet import GreatFET

FREQUENCY    = 1000
ADDRESS      = 0x39
WRITE_DATA   = bytes([0xac])
READ_LENGTH  = 2

BUFFER_SIZE  = 4096
TIMEOUT      = 10


gf = GreatFET()


# Start up the device's ADC.
dev_id = gf.i2c.transmit(ADDRESS, [0x80, 0x03], 0)


# Set the gain to 16x, and the fastest sample interval.
dev_id = gf.i2c.transmit(ADDRESS, [0x81, 0b10000], 0)


endpoint = gf.apis.i2c.stream_periodic_read(FREQUENCY, ADDRESS, READ_LENGTH, WRITE_DATA)
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
    gf.apis.i2c.stop_periodic_read()
    gf.comms.release_exclusive_access()


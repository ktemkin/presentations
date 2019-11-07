
# Turn on the device's ADC.
gf.i2c.transmit(0x39, [0x80, 0x03], 0)

# Set the fastest integration time and (for now) lowest gain.
gf.i2c.transmit(0x39, [0x81, 0x00], 0)

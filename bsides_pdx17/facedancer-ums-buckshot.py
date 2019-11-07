#!/usr/bin/env python3
#
# facedancer-ums-doublefetc.py
#
# "Double fetch" proof-of-concept for Facedancer
#

import re
import sys
import math

from facedancer import FacedancerUSBApp
from USBMassStorage import *


class BuckshotImage(FAT32DiskImage):

    TARGET_REGION_START = 10147  # specified by our root directory entry

    def __init__(self, wordlist, verbose=0):

        # Store copies of both of our firmware images. For now, we assume these are small enough
        # to fit nicely in memory.
        with open(wordlist, 'r') as f:
            self.names = f.read().split()

        # Call into our parent constructor.
        super().__init__(16 * 1024 * 1024, verbose)


    def _initialize_sector_handlers(self):
        super()._initialize_sector_handlers()
        self._register_sector_handler(lambda x : x >= self.TARGET_REGION_START and x <= self.TARGET_REGION_START + 127, "File Storage", self.handle_file_read)


    def handle_root_dir_read(self, address):
        """
            Returns a valid entry describing the root directory of our FAT filesystem.
            This allows us to present out firmware file to the target.
        """

        def bytes_as_hex(b, delim=" "):
            return delim.join(["%02x" % x for x in b])

        # Generate the volume label entry.
        response = self._generate_directory_entry(b'Facedancer ', 0, 0, flags=b'\x08')

        # Return a directory entry indicating our target firmware file.
        for index, name in enumerate(self.names):
            short_filename = self._short_filename_from_long(name)
            response += self._generate_long_directory_entries(name, short_filename)
            response += self._generate_directory_entry(short_filename, 10, 3 + index)

        return response


    def handle_fat_read(self, address):
        """
        Handles an access to the device's file allocaiton table.
        """

        response = b''

        # If this is the first sector, add our labels and root directory...
        if address == self.FAT_START:
            response  = b'\xF8\xFF\xFF\x0F' # media type = fat32 hard disk
            response += b'\xFF\xFF\xFF\x0F' # partition state
            response += b'\xFF\xFF\xFF\xFF' # root directory entry ends here
            response += b'\xFF\xFF\xFF\xFF' * 125 # every other file ends immediately

            # TODO: handle firmware that ends in the first sector?

        # ... otherwise, just generate the FAT entries for our firmware.
        else:
            response += b'\xFF\xFF\xFF\xFF' * 128 # every file ends immediately

        return response


    def handle_file_read(self, address):
        """
        Handles reads of the firmware itself.
        """

        file_offset = address - self.TARGET_REGION_START

        if file_offset < len(self.names):
            filename = self.names[file_offset]
            print("Read from: {}".format(filename))

        return "\0" * self.get_sector_size()




if len(sys.argv)==1:
    print("Usage: facedancer-ums-buckshot.py wordlist")
    sys.exit(1);

u = FacedancerUSBApp(verbose=0)
i = BuckshotImage(sys.argv[1], verbose=0)
d = USBMassStorageDevice(u, i, verbose=0)

d.connect()

try:
    d.run()
except KeyboardInterrupt:
    d.disconnect()

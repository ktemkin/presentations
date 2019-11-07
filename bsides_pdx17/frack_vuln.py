#!/usr/bin/env python3
#
# HorrorHacks for the FD demo at bsidesPDX
#

import sys
import hashlib

class SimpleDisk:

    MBR_SECTOR       = 0
    BPB_SECTOR       = 2048
    FSINFO_SECTOR    = 2049
    FAT_START        = 2080
    ROOT_DIR_SECTOR  = 10146
    FW_IMAGE_START   = 10147

    def __init__(self, name):
        self.name = name
        self.disk = open(name, 'rb', buffering=0)
        self.cache = {}

    def force_cache_drop(self):
        with open('/proc/sys/vm/drop_caches', 'w') as file:
            file.write('3\n')

    def read_sector(self, num):
        self.disk.seek(num * 512)
        return self.disk.read(512)

    def caching_read_sector(self, num):
        # Cache hit: read the data directly.
        if num in self.cache:
            return self.cache[num]

        # Read and cache our data.
        data = self.read_sector(num)
        self.cache[num] = data

        # So much easier when we don't have to worry about invalidation. ;)
        return data


    def do_startup_poking(self):
        self.caching_read_sector(self.MBR_SECTOR)
        self.caching_read_sector(self.BPB_SECTOR)
        self.caching_read_sector(self.FSINFO_SECTOR)

    def close(self):
        self.disk.close()


    def get_update_extents(self):
        # Read our root directory entry, and extract the location of the relevant FAT entry.
        dir = self.caching_read_sector(self.ROOT_DIR_SECTOR)

        # 'Parse' our directory entry.
        header   = dir[0:32]
        longname = dir[32:64]
        file     = dir[64:96]

        # Grab the cluster number that starts our FAT entry.
        cluster_high  = file[0x1A:0x1C]
        cluster_low   = file[0x14:0x16]

        size = int.from_bytes(file[0x1C:0x1C+4], byteorder='little')

        # Parse and return it.
        cluster = int.from_bytes(cluster_high + cluster_low,  byteorder='little')
        return cluster, size


    def get_file_clusters(self, fat, start, existing=None):

        # If we don't already have a list of clusters, create one.
        if existing is None:
            existing = []

        existing.append(start)

        # Grab the next cluster in the cluster chain...
        next_link = self.read_link_from_fat(fat, start)
        next_link = int.from_bytes(next_link, byteorder='little')

        # ... if we've hit a terminator, stop.
        if next_link >= 200000000: # XXX hax
            return existing

        # Otherwise, recurse.
        return self.get_file_clusters(fat, next_link, existing)


    def read_file_contents(self, clusters, length):

        data = b''

        for cluster in clusters:
            real_location = (cluster - 3) + self.FW_IMAGE_START
            data += self.caching_read_sector(real_location)

        return data[0:length]


    def read_fat(self):
        self.force_cache_drop()

        fat = b''

        # XXX this isn't the full FAT, we're just grabbing a section to make this quick
        for i in range(32):
            sector = self.FAT_START + (i * 512)
            fat += self.read_sector(sector)

        return fat

    def read_link_from_fat(self, fat, number):
        """ Read a single link from the cluster chain """
        offset = number * 4
        return fat[offset:offset+4]


    def read_update_file(self):
        start, length = self.get_update_extents()
        fat   = self.read_fat()

        clusters = self.get_file_clusters(fat, start)
        contents = self.read_file_contents(clusters, length)

        return contents

    def validate_update_file(self):
        import crc16

        contents = self.read_update_file()

        data = contents[0:-2]

        # For show only. :)
        hash = hashlib.sha256(contents).hexdigest()
        print("Accepting data with hash of {}".format(hash))

        checksum = int.from_bytes(contents[-2:], byteorder='big')
        actual_checksum = crc = crc16.crc16xmodem(data)

        return checksum == actual_checksum



disk = SimpleDisk(sys.argv[1])
disk.do_startup_poking()

# Validate the firmware to flash it...
print("Checking firmware before flashing...")
valid = disk.validate_update_file()


if valid:
    print("Firmware valid!")

    update = disk.read_update_file()

    hash = hashlib.sha256(update).hexdigest()
    print("Flashed data with hash of {}.".format(hash))
    print("All done!")


else:
    print('Firmware is invalid!')

disk.close()

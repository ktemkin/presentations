#!/usr/bin/env python

import sys
import yaml

if len(sys.argv) != 3:
    print("flowgraph scaler for demos on different-DPI machines")
    print(">>> hey, kate, why don't you just fix this in GRC?")
    print()
    print("usage: {} <flowgraph> <scale-factor>\n".format(sys.argv[0]))
    sys.exit(-1)


SCALE = float(sys.argv[2])
FLOWGRAPH = sys.argv[1]

# Parse the GRC flowgraph.
with open(FLOWGRAPH, 'r') as f:
    data = yaml.load(f, Loader=yaml.CLoader)

# Automatically scale each of our block positions.
# TODO: is there anything beyond blocks we need to scale?
for block in data['blocks']:
    for key, value in block['states'].items():
        if key == 'coordinate':
            value[0] *= SCALE
            value[1] *= SCALE

# Dump the GRC flowgraph back into its file.
output = yaml.dump(data, Dumper=yaml.CDumper)
with open(FLOWGRAPH, 'w') as f:
    f.write(output)

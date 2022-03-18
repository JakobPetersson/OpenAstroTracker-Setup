#!/usr/bin/env python3

import argparse


#
# Setup args parser
#

arg_parser = argparse.ArgumentParser(description='OAT Setup')

arg_parser.add_argument(
    'latitude',
    type=float,
    action='store',
    help="The latitude (decimal degrees), positive northern hemisphere, negative (-) for southern"
)

arg_parser.add_argument(
    'longitude',
    type=float,
    action='store',
    help="The longitude (decimal degrees), positive eastern hemisphere, negative (-) for western"
)

arg_parser.add_argument(
    'serial_port',
    type=str,
    nargs='?',
    default='/dev/ttyUSB0',
    help="The serial port path (default: %(default)s)"
)

args = arg_parser.parse_args()

#
# Print args
#

print("--- OAT Setup ---")
print(f"Serial port: {args.serial_port}")
print(f"Latitude: {args.latitude}\u00b0")
print(f"Longitude: {args.longitude}\u00b0")

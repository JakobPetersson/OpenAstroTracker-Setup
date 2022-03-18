#!/usr/bin/env python3

import argparse
import os
import serial

def oat_read_response_string(serial_port, command):
    response = serial_port.readline().decode('utf-8')

    # Expect response to end with '#'
    expected_hash = response[-1]
    if expected_hash != '#':
        raise Exception(f"Expected response from command '{command}' to end with '#', response was '{response}'")

    return response[:-1]


def oat_send_command(serial_port, command):
    serial_port.write(str.encode(command))


def oat_send_command_string(serial_port, command):
    oat_send_command(serial_port, command)
    return oat_read_response_string(serial_port, command)


def open_oat_connection(serial_port_path):
    print('')
    print('- Open OAT serial port -')

    # Disable serial port reset on port open
    print(f"Disabling #DTR for {serial_port_path}")
    os.system(f"stty -F {serial_port_path} -hupcl")

    # Open serial port
    serial_port = serial.Serial(serial_port_path, 19200, timeout = 1)

    # Check connection

    # :GVP#
    #      Description:
    #        Get the Product Name
    #      Returns:
    #        "OpenAstroTracker#"
    product_name = oat_send_command_string(serial_port, ':GVP#')

    # :GVN#
    #      Description:
    #        Get the Firmware Version Number
    #      Returns:
    #        "V1.major.minor#" from version.h
    firmware_version = oat_send_command_string(serial_port, ':GVN#')

    if len(product_name) <= 0 or len(firmware_version) <= 0 :
        print('Could not connect to OAT, exiting...')
        quit()
    
    print('OAT is connected!')
    print(f"Product Name: {product_name}")
    print(f"Firmware Version: {firmware_version}")

    return serial_port


def close_oat_connection(serial_port):
    print('')
    print('- Close OAT serial port -')

    # Close serial port
    serial_port.close()

    print('OAT is disconnected!')


#
# Setup args parser
#

arg_parser = argparse.ArgumentParser(description='OAT Setup')

arg_parser.add_argument(
    'latitude',
    type=float,
    action='store',
    help='The latitude (decimal degrees), positive northern hemisphere, negative (-) for southern'
)

arg_parser.add_argument(
    'longitude',
    type=float,
    action='store',
    help='The longitude (decimal degrees), positive eastern hemisphere, negative (-) for western'
)

arg_parser.add_argument(
    'serial_port',
    type=str,
    nargs='?',
    default='/dev/ttyUSB0',
    help='The serial port path (default: %(default)s)'
)

args = arg_parser.parse_args()

#
# Print args
#

print('--- OAT Setup ---')
print(f"Serial port: {args.serial_port}")
print(f"Latitude: {args.latitude}\u00b0")
print(f"Longitude: {args.longitude}\u00b0")

#
# Setup serial port connection
#

serial_port = open_oat_connection(args.serial_port)

#
# Close serial port connection
#

close_oat_connection(serial_port)

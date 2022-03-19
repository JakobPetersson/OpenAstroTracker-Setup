#!/usr/bin/env python3

import argparse
import os
import serial
from datetime import datetime


def oat_read_response(serial_port):
    return serial_port.readline().decode('utf-8')

def oat_send_command(serial_port, command):
    serial_port.write(str.encode(command))


def oat_read_response_status(serial_port, command):
    response = oat_read_response(serial_port)
    return len(response) > 0 and response[0] == '1'
        

def oat_send_command_status(serial_port, command):
    oat_send_command(serial_port, command)
    return oat_read_response_status(serial_port, command)


def oat_read_response_string(serial_port, command):
    response = oat_read_response(serial_port)

    # Expect response to end with '#'
    expected_hash = response[-1]
    if expected_hash != '#':
        raise Exception(f"Expected response from command '{command}' to end with '#', response was '{response}'")

    return response[:-1]


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


def oat_set_site_local_time(serial_port, current_datetime):
    formatted_time = current_datetime.strftime('%H:%M:%S')

    # :SLHH:MM:SS#
    #      Description:
    #        Set Site Local Time
    #      Information:
    #        This sets the local time of the timezone in which the mount is located.
    #      Returns:
    #        "1"
    #      Parameters:
    #        "HH" is hours
    #        "MM" is minutes
    #        "SS" is seconds
    if not oat_send_command_status(serial_port, f":SL{formatted_time}#"):
        print('Error setting Site Local Time...')
        quit()

    # :GL#
    #      Description:
    #        Get local time in 24h format
    #      Returns:
    #        "HH:MM:SS#"
    #      Parameters:
    #        "HH" are hours
    #        "MM" are minutes
    #        "SS" are seconds of the local time
    local_time_response = oat_send_command_string(serial_port, ':GL#')

    print(f"Site Local Time set to: {local_time_response}")


def oat_set_site_date(serial_port, current_datetime):
    formatted_date = current_datetime.strftime('%m/%d/%y')

    # :SCMM/DD/YY#
    #      Description:
    #        Set Site Date
    #      Information:
    #        This sets the date
    #      Returns:
    #        "1Updating Planetary Data#                              #"
    #      Parameters:
    #        "MM" is the month
    #        "DD" is the day
    #        "YY" is the year since 2000
    if not oat_send_command_status(serial_port, f":SC{formatted_date}#"):
        print('Error setting Site Date...')
        quit()

    # :GC#
    #      Description:
    #        Get current date
    #      Returns:
    #        "MM/DD/YY#"
    #      Parameters:
    #        "MM" is the month (1-12)
    #        "day" is the day (1-31)
    #        "year" is the lower two digits of the year
    current_date_response = oat_send_command_string(serial_port, ':GC#')

    if current_date_response != formatted_date:
        print(f"Error verifying Site Date... expected [{formatted_date}#], got [{current_date_response}]")
        quit()

    print(f"Site Date set to: {current_date_response}")


def oat_set_site_utc_offset(serial_port, current_datetime):
    iso_8601_parts = current_datetime.isoformat().split('T')
    if len(iso_8601_parts) != 2:
        print('Error setting UTC Offset...')
        quit()

    sign = '+'
    tz_split = iso_8601_parts[1].split(sign)
    if len(tz_split) != 2:
        sign = '-'
        tz_split = iso_8601_parts[1].split(sign)
        if len(tz_split) != 2:
            print('Error setting UTC Offset...')
            quit()

    tz_parts = tz_split[1].split(':')
    if len(tz_parts) != 2:
        print('Error setting UTC Offset...')
        quit()

    tz_hour = sign + tz_parts[0]

    # :SGsHH#
    #      Description:
    #        Set Site UTC Offset
    #      Information:
    #        This sets the offset of the timezone in which the mount is in hours from UTC.
    #      Returns:
    #        "1"
    #      Parameters:
    #        "s" is the sign
    #        "HH" is the number of hours
    if not oat_send_command_status(serial_port, f":SG{tz_hour}#"):
        print('Error setting UTC Offset...')
        quit()
        
    # :GG#
    #      Description:
    #        Get UTC offset time
    #      Returns:
    #        "sHH#"
    #      Parameters:
    #        "s" is the sign
    #        "HH" are the number of hours that need to be added to local time to convert to UTC time
    utc_offset_time_response = oat_send_command_string(serial_port, ':GG#')

    if utc_offset_time_response != tz_hour:
        print(f"Error verifying Site UTC Offset... expected [{tz_hour}], got [{utc_offset_time_response}]")
        quit()

    print(f"Site UTC Offset set to: {utc_offset_time_response}")


def oat_autohome_ra(serial_port):
    print()
    print('- AutoHome RA -')
    
    # :MHRxn#
    #      Description:
    #        Home RA stepper via Hall sensor
    #      Information:
    #        This attempts to find the hall sensor and to home the RA ring accordingly.
    #      Parameters:
    #        "x" is either 'R' or 'L' and determines the direction in which the search starts (L is CW, R is CCW).
    #        "n" (Optional) is the maximum number of hours to move while searching for the sensor location. Defaults to 2h. Limited to the range 1h-5h.
    #      Remarks:
    #        The ring is first moved 30 degrees (or the given amount) in the initial direction. If no hall sensor is encountered,
    #        it will move twice the amount (60 degrees by default) in the opposite direction.
    #        If a hall sensor is not encountered during that slew, the homing exits with a failure.
    #        If the sensor is found, it will slew to the middle position of the Hall sensor trigger range and then to the offset
    #        specified in the Home offset position (set with the ":XSHRnnnn#" command).
    #        If the RA ring is positioned such that the Hall sensor is already triggered when the command is received, the mount will move
    #        the RA ring off the trigger in the opposite direction specified for a max of 15 degrees before searching 30 degrees in the
    #        specified direction.
    #      Returns:
    #        "1" returns if search is started
    #        "0" if homing has not been enabled in the local config
    if not oat_send_command_status(serial_port, ':MHRR#'):
        print('RA Auto Home is not enabled...')
        return

    print('RA Auto Home search started...')
    input('Press ENTER when RA is homed!')

    # :SHP#
    #      Description:
    #        Set Home Point
    #      Information:
    #        This sets the current orientation of the scope as its home point.
    #      Returns:
    #        "1"
    if not oat_send_command_status(serial_port, ':SHP#'):
        print('Error setting Home Point...')
        quit()

    print('Current orientation set as Home Point')


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
# Set Site Local Time, Date and UTC Offset
#

print("")
print("- Set Site Local Time -")
now = datetime.now().astimezone()
oat_set_site_local_time(serial_port, now)
oat_set_site_date(serial_port, now)
oat_set_site_utc_offset(serial_port, now)

#
# AutoHome RA
#

oat_autohome_ra(serial_port)

#
# Close serial port connection
#

close_oat_connection(serial_port)

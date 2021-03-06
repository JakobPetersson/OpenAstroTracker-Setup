#!/usr/bin/env python3

import argparse
import math
import os
import re
import serial
import time
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

    # :I#
    #      Description:
    #        Initialize Scope
    #      Information:
    #        This puts the Arduino in Serial Control Mode and displays RA on line 1 and
    #        DEC on line 2 of the display. Serial Control Mode can be ended manually by
    #        pressing the SELECT key, or programmatically with the :Qq# command.
    #      Returns:
    #        nothing
    oat_send_command(serial_port, ':I#')

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


def oat_set_site_latitude(serial_port, latitude):
    pat = re.compile(r"^[-\+][0-9][0-9]\*[0-9][0-9]$")

    if not re.fullmatch(pat, latitude):
        print('Error, latitude not in correct format')
        quit()

    lat_split = latitude.split('*')
    
    lat_deg = lat_split[0]
    lat_deg_int = int(lat_deg)
    
    lat_min = lat_split[1]
    lat_min_int = int(lat_min)

    if ((lat_deg_int > 90 or lat_deg_int < -90) or
        (lat_deg_int == 90 and lat_min_int > 0) or
        (lat_min_int > 60)):
        print('Error, latitude not in correct value range')
        quit()

    #
    # :StsDD*MM#
    #      Description:
    #        Set Site Latitude
    #      Information:
    #        This sets the latitude of the location of the mount.
    #      Returns:
    #        "1" if successfully set
    #        "0" otherwise
    #      Parameters:
    #        "s" is the sign ('+' or '-')
    #        "DD" is the degree (90 or less)
    #        "MM" is minutes
    #
    if not oat_send_command_status(serial_port, f":St{latitude}#"):
        print('Error setting Site Latitude...')
        quit()

    # :Gt#
    #      Description:
    #        Get Site Latitude
    #      Returns:
    #        "sDD*MM#"
    #      Parameters:
    #        "s" is + or -
    #        "DD" is the latitude in degrees
    #        "MM" the minutes
    site_latitude_response = oat_send_command_string(serial_port,':Gt#')

    if site_latitude_response != latitude:
        print(f"Error verifying Site Latitude... expected [{latitude}], got [{site_latitude_response}]")
        quit()

    print(f"Site Latitude set to: {lat_deg}\u00b0{lat_min}' ({site_latitude_response})")


def oat_set_site_longitude(serial_port, longitude):
    pat = re.compile(r"^[-\+]([0-9])?([0-9])[0-9]\*[0-9][0-9]$")

    if not re.fullmatch(pat, longitude):
        print('Error, longitude not in correct format')
        quit()

    long_split = longitude.split('*')

    long_deg = long_split[0]
    long_deg_int = int(long_deg)
    long_min = long_split[1]
    long_min_int = int(long_min)

    if ((long_deg_int > 180 or long_deg_int < -180) or
        (long_deg_int == 180 and long_min_int > 0) or
        (long_deg_int == -180 and long_min_int > 0) or
        (long_min_int > 60)):
        print('Error, longitude not in correct value range')
        quit()

    # :SgsDDD*MM#
    #      Description:
    #        Set Site Longitude
    #      Information:
    #        This sets the longitude of the location of the mount.
    #      Returns:
    #        "1" if successfully set
    #        "0" otherwise
    #      Parameters:
    #        "s" (optional) is the sign of the longitude (see Remarks)
    #        "DDD" is the degrees
    #        "MM" is the minutes
    #      Remarks:
    #        When a sign is provided, longitudes are interpreted as given, with zero at Greenwich but negative coordinates going east (opposite of normal cartographic coordinates)
    #        When a sign is not provided, longitudes are from 0 to 360 going WEST with 180 at Greenwich. So 369 is 179W and 1 is 179E. 190 would be 10W and 170 would be 10E.
    if not oat_send_command_status(serial_port, f":Sg{longitude}#"):
        print('Error setting Site Longitude...')
        quit()

    # :Gg#
    #      Description:
    #        Get Site Longitude
    #      Returns:
    #        "sDDD*MM#"
    #      Parameters:
    #        "s" is the sign of the longitude
    #        "DDD" is the longitude in degrees
    #        "MM" the minutes
    #      Remarks:
    #        Note that this is the actual longitude, but east coordinates are negative (opposite of normal cartographic coordinates)
    site_longitude_response = oat_send_command_string(serial_port, ':Gg#')

    if site_longitude_response != longitude:
        print(f"Error verifying Site Longitude... expected [{longitude}], got [{site_longitude_response}]")
        quit()

    print(f"Site Longitude set to: {long_deg}\u00b0{long_min}' ({site_longitude_response})")


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
        print(f"Error verifying Site Date... expected [{formatted_date}], got [{current_date_response}]")
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
    #        Get offset to UTC time
    #      Returns:
    #        "sHH#"
    #      Parameters:
    #        "s" is the sign
    #        "HH" is the number of hours
    #      Remarks
    #        Note that this is NOT simply the timezone offset you are in (like -8 for Pacific Standard Time), it is the negative of it. So how many hours need to be added to your local time to get to UTC.
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

    # Wait for OAT to complete homing
    while True:
        time.sleep(0.5)

        # :GX#
        #      Description:
        #        Get Mount Status
        #      Information:
        #         String reflecting the mounts' status. The string is a comma-delimited list of statuses
        #      Returns:
        #        "Idle,--T--,11219,0,927,071906,+900000,#"
        #      Parameters:
        #        [0] The mount status. One of 'Idle', 'Parked', 'Parking', 'Guiding', 'SlewToTarget', 'FreeSlew', 'ManualSlew', 'Tracking', 'Homing'
        #        [1] The motion state.
        #        [2] The RA stepper position
        #        [3] The DEC stepper position
        #        [4] The Tracking stepper position
        #        [5] The current RA position
        #        [6] The current DEC position
        #      Remarks:
        #        The motion state
        #        First character is RA slewing state ('R' is East, 'r' is West, '-' is stopped).
        #        Second character is DEC slewing state ('d' is North, 'D' is South, '-' is stopped).
        #        Third character is TRK slewing state ('T' is Tracking, '-' is stopped).
        #        Fourth character is AZ slewing state ('Z' and 'z' is adjusting, '-' is stopped).
        #        Fifth character is ALT slewing state ('A' and 'a' is adjusting, '-' is stopped).
        #        Az and Alt are optional. The string may only be 3 characters long
        status_response = oat_send_command_string(serial_port, ':GX#')

        status_split = status_response.split(',')
        mount_state = status_split[0]
        print(f"State: {mount_state}")

        if mount_state != 'Homing':
            break

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
    '--latitude',
    type=str,
    action='store',
    default='+51*28',
    help='The latitude sDDD*MM, positive (+) for northern hemisphere, negative (-) for southern (default: %(default)s)'
)

arg_parser.add_argument(
    '--longitude',
    type=str,
    action='store',
    default='+00*00',
    help='The longitude sDD*MM, positive (+) for western hemisphere, negative (-) for eastern (default: %(default)s)'
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
print(f"Latitude: {args.latitude}")
print(f"Longitude: {args.longitude}")

#
# Setup serial port connection
#

serial_port = open_oat_connection(args.serial_port)

#
# Set Site Coordinates
#

print('')
print('- Set Site Coordinates -')
oat_set_site_latitude(serial_port, args.latitude)
oat_set_site_longitude(serial_port, args.longitude)

#
# Set Site Local Time, Date and UTC Offset
#

print('')
print('- Set Site Local Time -')
now = datetime.now().astimezone()
oat_set_site_utc_offset(serial_port, now)
oat_set_site_local_time(serial_port, now)
oat_set_site_date(serial_port, now)

#
# AutoHome RA
#

oat_autohome_ra(serial_port)

#
# Close serial port connection
#

close_oat_connection(serial_port)

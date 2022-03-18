# OpenAstroTracker-Setup

Python scripts to setup and align [OpenAstroTracker](https://openastrotech.com/) when used with Linux. (Tested with [Astroberry](https://www.astroberry.io))


## Prerequisites:

* Python 3

## `oat_setup.py`

### Usage

```shell
./oat_setup.py --help
usage: oat_setup.py [-h] latitude longitude [serial_port]

OAT Setup

positional arguments:
  latitude     The latitude (decimal degrees), positive northern hemisphere, negative (-) for southern
  longitude    The longitude (decimal degrees), positive eastern hemisphere, negative (-) for western
  serial_port  The serial port path (default: /dev/ttyUSB0)

optional arguments:
  -h, --help   show this help message and exit
```

### Example

```shell
./oat_setup.py 59.33 18.07 /dev/ttyUSB0
```

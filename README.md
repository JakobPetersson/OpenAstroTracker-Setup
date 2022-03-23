# OpenAstroTracker-Setup

Python scripts to setup and align [OpenAstroTracker](https://openastrotech.com/) when used with Linux. (Tested with [Astroberry](https://www.astroberry.io))


## Prerequisites:

* Python 3

## `oat_setup.py`

### Usage

```shell
./oat_setup.py --help
usage: oat_setup.py [-h] [--latitude LATITUDE] [--longitude LONGITUDE]
                    [serial_port]

OAT Setup

positional arguments:
  serial_port           The serial port path (default: /dev/ttyUSB0)

optional arguments:
  -h, --help            show this help message and exit
  --latitude LATITUDE   The latitude sDDD*MM, positive (+) for northern
                        hemisphere, negative (-) for southern (default:
                        +51*28)
  --longitude LONGITUDE
                        The longitude sDD*MM, positive (+) for western
                        hemisphere, negative (-) for eastern (default: +00*00)
```

### Example

```shell
./oat_setup.py --latitude="+59*19" --longitude="+18*04" /dev/ttyUSB0
```

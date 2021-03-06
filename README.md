
# Preseed to Autoinstall

Objective: Ingest Debian preseed format file(s), and provide compatible
Subiquity autoinstall in response.

Project Status: Closing on a usable feature set.  Some basic support is present
but there is room for improvement.  Not yet very well tested.  Netplan output
probably not yet correct.

## Usage
    usage: autoinstall-generator.py [-h] [-d] infile [outfile]

    positional arguments:
      infile       Debian install preseed file, or a dash to read stdin
      outfile      Subiquity autoinstall yaml

    optional arguments:
      -h, --help   show this help message and exit
      -d, --debug  include commented out debug output explaining the conversions
                   performed

## Feedback

Please direct bugs and feature requests to the project on
[Launchpad](https://launchpad.net/autoinstall-generator).

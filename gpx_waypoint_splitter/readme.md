# GPX Waypoint Splitter

I had a GPX file with more than 15k waypoints I needed to import to a service that only allowed 1k items per upload. This will split a gpx file into multiple files containing however many waypoints you specify.

Thanks Claude!

## Usage

Basic usage (defaults to 1000 waypoints per file, will output MYFILE_001.gpx, MYFILE_002.gpx, etc):

`python gpx_waypoint_splitter.py MYFILE.gpx`

Change the base output filename (new_name_001.gpx, new_name_002.gpx, etc):

`python gpx_waypoint_splitter.py MYFILE.gpx new_name`

Change waypoints per file by passing the number desired to the -w flag, 500 in this case:

`python gpx_waypoint_splitter.py MYFILE.gpx -w 500`

If you wanted to output new_name_001.gpx and new_name_002.gpx etc broken into files with 2000 waypoints each you'd use the following:

`python gpx_waypoint_splitter.py MYFILE.gpx new_name -w 2000`

## MacOS Notes

You can install Python via the [homebrew](https://brew.sh/) package manager.

Unless you create an alias in your shell, you'll probably need to replace 'python' with 'python3' in the commands above.
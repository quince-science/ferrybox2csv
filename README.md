# ferrybox2csv
Convert a folder of Ferrybox files to a single CSV file.

Ferrybox systems produce their output with one file per variable.
This script converts a Ferrybox output to normal CSV files.

Main features:
- Handles all files in one folder, or files in sub-folders
- Strips headers from files
- Extracts the main value (second column) from each file
- Extracts Longitude and Latitude
- Aligns all values to their timestamps
- Outputs CSV files at the same time granularity as the input data (e.g. one CSV file per day)


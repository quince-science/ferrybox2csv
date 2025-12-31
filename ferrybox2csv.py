import argparse
import glob
import os
import re
import numpy as np
import pandas as pd

INVALID_MODE = -1
FILES_MODE = 0
FOLDERS_MODE = 1

def test_files(folder):
    # Input folder should contain just files or just folders
    in_files = glob.glob(f'{folder}/*')

    has_files = False
    has_folders = False

    for file in in_files:
        if os.path.isfile(file):
            has_files = True
        elif os.path.isdir(file):
            has_folders = True
            sub_folder = glob.glob(f'{file}/*')
            for sub_file in sub_folder:
                if os.path.isdir(sub_file):
                    exit(f'Found sub-folder "{sub_file}" - subfolders are not allowed')

        if has_files and has_folders:
            exit('Input folder must contain all files or all folders')

    return FILES_MODE if has_files else FOLDERS_MODE


def get_dates(folder):
    dates = set()

    for file in glob.glob(f'{folder}/**', recursive=True):
        if os.path.isfile(file):
            extract = re.search(r'.*_(\d+).txt', os.path.basename(file))
            dates.add(extract.group(1))

    return dates

def get_header_count(file):
    
    header_rows = 0
    header_complete = False
    
    with open(file, encoding='cp1252') as fin:
        lines = fin.readlines()
        for line in lines:
            header_rows += 1
            if '$DATASETS' in line:
                header_complete = True
                break

        if not header_complete:
            exit(f'Failed to read header from {file}')                

    return header_rows


# Command line arguments
parser = argparse.ArgumentParser(prog='ferrybox2csv',
    description='Convert Ferrybox output files to CSV files')

parser.add_argument('input_folder',
    help='Folder containing Ferrybox files')

parser.add_argument('output_folder',
    help='Folder for output files')

args = parser.parse_args()

# Check that the files/folders are set up how we expect
mode = test_files(args.input_folder)

# Get the variables and dates of the files
dates = get_dates(args.input_folder)

# Collect all data for each date in turn
for date in sorted(dates):
    print(date)

    date_df = None

    date_files = glob.glob(f'{args.input_folder}/**/*_{date}.txt', recursive=True)

    position_found = False

    for file in date_files:
        # Work out where the preamble ends
        header_rows = get_header_count(file)

        # Load the file into a DataFrame
        file_df = pd.read_csv(file, sep='\t', skiprows=header_rows, header=[0, 1], parse_dates=[0], encoding='cp1252')
        file_df.columns = file_df.columns.droplevel(1)
        file_df.rename(columns={'$Timestamp' : 'Timestamp'}, inplace=True)

        # The column for the variable is always the second column
        var_column = file_df.columns[1]

        # Build the list of columns to keep
        keep_columns = ['Timestamp']
        
        # Add the position if we haven't already got it
        if not position_found:
            keep_columns += ['Longitude', 'Latitude']
            position_found = True

        keep_columns += [var_column]

        # Drop all other columns
        file_df = file_df[keep_columns]

        # Merge with the rest of the data from this date
        if date_df is None:
            date_df = file_df
        else:
            date_df = pd.merge(date_df, file_df, on='Timestamp', how='outer').sort_values('Timestamp').reset_index(drop=True)

    # Reorder columns so they're consistent for all files
    fixed_columns = ['Timestamp', 'Longitude', 'Latitude']
    var_columns = sorted([c for c in date_df.columns if c not in fixed_columns])
    date_df = date_df[fixed_columns + var_columns]

    date_df.to_csv(f'{args.output_folder}/{date}.csv', date_format='%Y-%m-%dT%H:%M:%SZ', index=False)

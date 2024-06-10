#!/usr/bin/env bash
echo "Running cleanup script..."
# set the directory path to the directory you want to clean up
directory_path="/path/to/your/directory"
# remove all files and directories in the directory
cd $directory_path
rm -rf *
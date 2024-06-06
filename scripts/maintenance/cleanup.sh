#!/usr/bin/env bash
echo "Running cleanup script..."
# set the directory path to the directory you want to clean up
directory_path="/path/to/your/directory"
# cleanup the cloned repository and remove the LFS files, don't delete the repository itself
cd $directory_path
rm -rf *
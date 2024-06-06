#!/usr/bin/env bash

# TODO Implement the revert-repository-changes.sh script

$directory_path=$1

# cleanup the cloned repository, don't delete the repository itself
cd $directory_path

echo "Reverting the repository changes..."

## uncomment to remove the LFS files
# git lfs uninstall
# git lfs untrack
# git lfs uninit
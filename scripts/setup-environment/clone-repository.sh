#!/usr/bin/env bash

echo "Cloning the repository..."

# boolean variable
use_private_repo=true
is_production_mode=false

# specify the branch
branch="ccxt-sora"
checkoutPath = '/ccxt'

# select the repository url
private_repository_url="***REMOVED***"
public_repository_url="https://github.com/ccxt/ccxt.git"

# choose the repository based on the boolean
if $use_private_repo ; then
    repository_url=$private_repository_url
else
    repository_url=$public_repository_url
fi

# clone the repository, if we are in production mode we only need the latest commit
if $is_production_mode ; then
    # checkout source from github repository, latest commit should be enough, checkout our specific branch
    git clone --branch $branch --depth 1 $repository_url $checkoutPath
else
    # in dev mode we want all of our branches history and tags
    git clone --branch $branch $repository_url $checkoutPath
fi

# uncomment to pull the LFS files 
# cd $(basename "$repository_url" .git) #navigate into the cloned repository
# git lfs pull
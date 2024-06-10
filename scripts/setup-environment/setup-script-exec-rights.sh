#!/usr/bin/env bash

# make sure our scripts can execute
echo "setting exec rights on our scripts..."

#chmod 755 /ccxt/pmx-dev/scripts/setup-environment/setup-script-exec-rights.sh

# Recursively add execution permissions to all files in the directory
chmod -R 755 /pmx-dev/scripts/

echo "...done!"
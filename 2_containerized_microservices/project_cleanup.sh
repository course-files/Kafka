#!/bin/bash

set -e  # Exit immediately if a command fails

echo "Deleting volume directories..."

# Safety check: ensure we are in the correct project directory
if [ ! -d "./container-volumes" ]; then
    echo "Error: ./container-volumes does not exist. Aborting."
    exit 1
fi

# Remove everything in one controlled operation
rm -rf ./container-volumes

echo "Cleanup complete."
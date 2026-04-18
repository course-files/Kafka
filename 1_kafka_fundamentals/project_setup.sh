#!/bin/bash

set -euo pipefail

# Resolve script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/container-volumes"

echo "Creating volume directories..."

# Prevent accidental overwrite of unexpected file
if [ -e "$BASE_DIR" ] && [ ! -d "$BASE_DIR" ]; then
    echo "Error: $BASE_DIR exists but is not a directory. Aborting."
    exit 1
fi

if [ -L "$BASE_DIR" ]; then
    echo "Error: $BASE_DIR is a symbolic link. Aborting."
    exit 1
fi

# Optional: warn if reusing existing data
if [ -d "$BASE_DIR" ] && compgen -A file "$BASE_DIR" > /dev/null; then
    echo "Warning: Existing data detected in $BASE_DIR"
fi

# Create directories
mkdir -p \
    "$BASE_DIR/kafka/var-lib-kafka-data"

echo "Setting permissions..."

# Safe permission handling
chmod -R 775 "$BASE_DIR"

echo "Done. You may now proceed to the next step."
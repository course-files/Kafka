#!/bin/bash

set -euo pipefail

# Resolve script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/container-volumes"

echo "Run the following command to shutdown the Docker containers first:"
echo "docker-compose down -v"
# Optional confirmation (good for a learning environment, bad for automation)
read -r -p "Did your run 'docker-compose down -v' first? (y/N): " confirm
if [[ "$confirm" != "N" ]]; then
    echo "Aborted to give you a chance to run 'docker-compose down -v' first."
    exit 0
fi
echo "Deleting volume directories..."

# Ensure directory exists
if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Expected directory $BASE_DIR does not exist. Aborting."
    exit 1
fi

# Ensure it is NOT a symlink
if [ -L "$BASE_DIR" ]; then
    echo "Error: $BASE_DIR is a symbolic link. Aborting."
    exit 1
fi

# Ensure it is exactly where we expect (no substrings)
EXPECTED_DIR="$SCRIPT_DIR/container-volumes"
if [ "$BASE_DIR" != "$EXPECTED_DIR" ]; then
    echo "Error: Directory mismatch. Aborting."
    exit 1
fi

# Prevent catastrophic paths
case "$BASE_DIR" in
    ""|"/"|"/home"|"/root")
        echo "Error: Unsafe path detected. Aborting."
        exit 1
        ;;
esac

# Optional confirmation (good for a learning environment, bad for automation)
read -r -p "Are you sure you want to delete $BASE_DIR? (y/N): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "Aborted."
    exit 0
fi

# Controlled deletion
rm -rf -- "$BASE_DIR"

echo "Cleanup complete."
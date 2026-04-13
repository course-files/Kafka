#!/bin/bash

set -e

# Resolve the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/container-volumes"

echo "Creating volume directories..."

mkdir -p "$BASE_DIR/kafka1/data"
mkdir -p "$BASE_DIR/kafka2/data"
mkdir -p "$BASE_DIR/kafka3/data"
mkdir -p "$BASE_DIR/postgres/data"

echo "Setting permissions..."
chmod -R 755 "$BASE_DIR"

echo "Done. You may now proceed to the next step in the lab."
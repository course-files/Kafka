#!/bin/bash

set -euo pipefail

# Resolve script location (assumed to be in repo root or subdirectory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define repository root (adjust if script is in subdirectory)
REPO_ROOT="$SCRIPT_DIR"

echo "Scanning for virtual environment directories in:"
echo "$REPO_ROOT"
echo "---------------------------------------------"

# Safety checks
if [ ! -d "$REPO_ROOT" ]; then
    echo "Error: Repository root does not exist. Aborting."
    exit 1
fi

if [ -L "$REPO_ROOT" ]; then
    echo "Error: Repository root is a symbolic link. Aborting."
    exit 1
fi

case "$REPO_ROOT" in
    ""|"/"|"/home"|"/root")
        echo "Error: Unsafe repository path detected. Aborting."
        exit 1
        ;;
esac

# Find matching directories (non-recursive)
mapfile -t VENV_DIRS < <(find "$REPO_ROOT" -maxdepth 1 -type d -name ".venv*" -print)

if [ ${#VENV_DIRS[@]} -eq 0 ]; then
    echo "No .venv* directories found. Nothing to clean."
    exit 0
fi

echo "Found the following directories:"
for dir in "${VENV_DIRS[@]}"; do
    echo " - $dir"
done

echo "---------------------------------------------"

# Confirm each directory individually
for dir in "${VENV_DIRS[@]}"; do

    # Extra safety: ensure directory is exactly under repo root
    if [[ "$(dirname "$dir")" != "$REPO_ROOT" ]]; then
        echo "Skipping unexpected path: $dir"
        continue
    fi

    # Ensure not a symlink
    if [ -L "$dir" ]; then
        echo "Skipping symbolic link: $dir"
        continue
    fi

    read -r -p "Delete directory '$dir'? (y/N): " confirm
    if [[ "$confirm" == "y" ]]; then
        rm -rf -- "$dir"
        echo "Deleted: $dir"
    else
        echo "Skipped: $dir"
    fi
done

echo "Cleanup complete."
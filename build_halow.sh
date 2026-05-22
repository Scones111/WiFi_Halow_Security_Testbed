#!/bin/bash

# Script to build and install gr-ieee802-11ah project
# This script wraps the build_and_install.sh script located in gr-ieee802-11ah/

# Exit on any error
set -e

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -j JOBS   Number of parallel jobs for make (default: 4)"
    echo "  -c        Clean the build directory and uninstall before building"
    echo "  -h        Display this help message"
    echo ""
    echo "Example: $0 -j 8 -c"
    exit 1
}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HALOW_DIR="$SCRIPT_DIR/gr-ieee802-11ah"

# Check if the project directory exists
if [ ! -d "$HALOW_DIR" ]; then
    echo "[ERROR] gr-ieee802-11ah directory not found at $HALOW_DIR"
    exit 1
fi

# Check if build_and_install.sh exists
BUILD_SCRIPT="$HALOW_DIR/build_and_install.sh"
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "[ERROR] build_and_install.sh not found at $BUILD_SCRIPT"
    exit 1
fi

# Make build_and_install.sh executable
chmod +x "$BUILD_SCRIPT"

# Log message
log() {
    echo "[INFO] $1"
}

# Default values
JOBS=4
CLEAN_FLAG=""

# Parse command-line options
while getopts "j:ch" opt; do
    case $opt in
        j) JOBS="$OPTARG" ;;
        c) CLEAN_FLAG="-c" ;;
        h) usage ;;
        ?) usage ;;
    esac
done

# Log build information
log "Building gr-ieee802-11ah project..."
log "Project directory: $HALOW_DIR"
log "Parallel jobs: $JOBS"
if [ -n "$CLEAN_FLAG" ]; then
    log "Clean build enabled"
fi

# Navigate to the project directory
cd "$HALOW_DIR" || { echo "[ERROR] Failed to navigate to $HALOW_DIR"; exit 1; }

# Run the build_and_install.sh script with passed arguments
log "Executing build_and_install.sh..."
bash "$BUILD_SCRIPT" -j "$JOBS" $CLEAN_FLAG

if [ $? -eq 0 ]; then
    log "Build and installation completed successfully!"
else
    echo "[ERROR] Build and installation failed"
    exit 1
fi

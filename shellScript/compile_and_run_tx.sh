#!/bin/bash

# Script to compile GNU Radio flowgraphs (halow_phy_hier.grc and halow_tx.grc) and run halow_tx.py
# This script always performs fresh compilation to ensure the latest updates

# Exit on any error
set -e

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -r            Run the compiled halow_tx script after compilation"
    echo "  -h            Display this help message"
    echo ""
    echo "Example: $0         # Compile both flowgraphs"
    echo "Example: $0 -r      # Compile both flowgraphs and run halow_tx"
    exit 1
}

# Function to log messages
log() {
    echo "[INFO] $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR/gr-ieee802-11ah/examples"

# Check if examples directory exists
if [ ! -d "$EXAMPLES_DIR" ]; then
    echo "[ERROR] examples directory not found at $EXAMPLES_DIR"
    exit 1
fi

# Default values
RUN_SCRIPT=false
OUTPUT_DIR="$EXAMPLES_DIR"

# Parse command-line options
while getopts "rh" opt; do
    case $opt in
        r) RUN_SCRIPT=true ;;
        h) usage ;;
        ?) usage ;;
    esac
done

# Check if grcc is installed
if ! command_exists grcc; then
    echo "[ERROR] grcc (GNU Radio Companion compiler) not found"
    echo "Please install GNU Radio: sudo apt-get install gnuradio"
    exit 1
fi

log "Compiling flowgraphs for halow_tx..."
log "Examples directory: $EXAMPLES_DIR"

# Navigate to examples directory
cd "$EXAMPLES_DIR" || { echo "[ERROR] Failed to navigate to $EXAMPLES_DIR"; exit 1; }

# Define flowgraphs to compile in order
HALOW_PHY_HIER_FLOWGRAPHS="halow_phy_hier.grc"
HALOW_TX_FLOWGRAPHS="halow_tx.grc"


PHY_OUTPUT_DIR="$HOME/.local/state/gnuradio"

# Compile each flowgraph
for grc_file in "${HALOW_PHY_HIER_FLOWGRAPHS}" "${HALOW_TX_FLOWGRAPHS}"; do
    if [ ! -f "$grc_file" ]; then
        echo "[ERROR] Flowgraph $grc_file not found in $EXAMPLES_DIR"
        exit 1
    fi
    
    log "Compiling $grc_file..."
    if [ "$grc_file" == "halow_phy_hier.grc" ]; then
        grcc -o "$PHY_OUTPUT_DIR" "$EXAMPLES_DIR/$grc_file"
    fi
    if [ "$grc_file" == "halow_tx.grc" ]; then
        grcc -o "$EXAMPLES_DIR" "$EXAMPLES_DIR/$grc_file"
    fi
done

log "Flowgraph compilation completed successfully!"

echo "$RUN_SCRIPT"

# Run the script if requested
if [ "$RUN_SCRIPT" = true ]; then
    SCRIPT_NAME="halow_tx.py"
    SCRIPT_PATH="$OUTPUT_DIR/$SCRIPT_NAME"
    
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "[ERROR] Compiled script $SCRIPT_PATH not found"
        exit 1
    fi
    
    log "Running $SCRIPT_NAME..."
    /usr/bin/python3 "$SCRIPT_PATH" "$@"
else
    log "To run the compiled script, use: /usr/bin/python3 $OUTPUT_DIR/halow_tx.py"
fi

cd ../..
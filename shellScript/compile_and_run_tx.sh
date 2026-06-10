#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
EXAMPLES_DIR="$BASE_DIR/gr-ieee802-11ah/examples"

PHY="halow_phy_hier.grc"
TX="halow_tx.grc"

echo "[INFO] Entering $EXAMPLES_DIR"
cd "$EXAMPLES_DIR"

echo "[INFO] Compiling PHY..."
grcc -o "$HOME/.local/state/gnuradio" "$PHY"

echo "[INFO] Compiling TX..."
grcc -o "$EXAMPLES_DIR" "$TX"

echo "[INFO] Running TX..."
python3 "$EXAMPLES_DIR/halow_tx.py"
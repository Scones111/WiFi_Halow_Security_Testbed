#!/bin/bash
set -e

exec_folder="$(cd .. && pwd)"
grc_folder="$exec_folder/gr-ieee802-11ah/examples"



PHY="halow_phy_hier.grc"
TX="halow_tx.grc"

cd "$grc_folder"

grcc -o "$HOME/.local/state/gnuradio" "$PHY"

grcc -o "$grc_folder" "$TX"

echo "[INFO] Running TX..."
/usr/bin/python3 "$grc_folder/halow_tx.py"


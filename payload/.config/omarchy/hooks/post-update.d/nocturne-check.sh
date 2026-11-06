#!/bin/sh
# Omarchy runs this after migrations and restarts. No package/config writes.
exec python3 "$HOME/.local/lib/omarchy-nocturne/check-compatibility.py" --notify

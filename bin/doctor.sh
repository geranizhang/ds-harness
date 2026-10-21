#!/bin/bash
# Health check for this machine's ds-harness install. See hosts/doctor.py.
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/hosts/doctor.py" "$@"

#!/bin/bash
set -e

mkdir -p /data/configdb
if [ ! -f /data/configdb/keyfile ]; then
    echo "[INIT] generating keyfile..."
    openssl rand -base64 756 > /data/configdb/keyfile
    chmod 600 /data/configdb/keyfile
    chown mongodb:mongodb /data/configdb/keyfile
fi
exec docker-entrypoint.sh "$@"

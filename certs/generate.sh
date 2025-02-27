#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -f "$SCRIPT_DIR"/*.key
rm -f "$SCRIPT_DIR"/*.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout "$SCRIPT_DIR"/server.key -out "$SCRIPT_DIR"/server.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout "$SCRIPT_DIR"/client.key -out "$SCRIPT_DIR"/client.pem

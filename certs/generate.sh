#!/bin/bash

rm -f ./*.key
rm -f ./*.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout server.key -out server.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout client.key -out client.pem

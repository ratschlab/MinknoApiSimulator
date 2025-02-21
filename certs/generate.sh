#!/bin/bash

rm -f ./*.key
rm -f ./*.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout server.key -out server.pem
openssl req -x509 -newkey rsa:2048 -nodes -subj '/CN=localhost' -keyout client.key -out client.pem

# Generate private key
openssl genpkey -algorithm RSA -out server.key

# Generate self-signed certificate
openssl req -x509 -key server.key -out server.crt -days 365

############# For mutual TLS (mTLS) -

# Generate a private key for the CA
openssl genpkey -algorithm RSA -out rootCA.key

# Generate a self-signed CA certificate
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 365 -out rootCA.crt

# Generate private key for the server
openssl genpkey -algorithm RSA -out server.key

# Create a certificate signing request (CSR)
openssl req -new -key server.key -out server.csr

# Generate the server certificate signed by the CA
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out server.crt -days 365 -sha256

# Generate private key for the client
openssl genpkey -algorithm RSA -out client.key

# Create a certificate signing request (CSR) for the client
openssl req -new -key client.key -out client.csr

# Generate the client certificate signed by the CA
openssl x509 -req -in client.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out client.crt -days 365 -sha256


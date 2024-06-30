#!/bin/bash

if [ -e capsman.key ]; then
  echo "capsman.key already exists"
  exit 1
fi

openssl genrsa -out capsman.key 2048
openssl req -new -sha256 -key capsman.key -subj "/CN=capsman" -out capsman.csr \
   -addext "keyUsage = digitalSignature, keyEncipherment, dataEncipherment"
openssl x509 -req -in capsman.csr -CA capsman-ca.crt -CAkey capsman-ca.key -out capsman.crt -days 10000 -sha256 -copy_extensions "copyall"
rm -f capsman.csr

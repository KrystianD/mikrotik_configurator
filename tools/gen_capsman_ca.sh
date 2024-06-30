#!/bin/bash

if [ -e capsman-ca.key ]; then
  echo "capsman-ca.key already exists"
  exit 1
fi

openssl genrsa -out capsman-ca.key 2048
openssl req -x509 -new -nodes -key capsman-ca.key -sha256 -days 10000 -out capsman-ca.crt -subj "/CN=capsman-ca" \
   -addext "basicConstraints = critical,CA:true" \
   -addext "keyUsage = digitalSignature, keyEncipherment, dataEncipherment, cRLSign, keyCertSign"

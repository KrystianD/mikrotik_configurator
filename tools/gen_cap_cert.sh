#!/bin/bash

CAP=$1

if [ "$CAP" = "" ]; then
  echo "usage: $0 <cap-name>"
  exit 1
fi

CAP_KEY="${CAP}.key"
CAP_CERT="${CAP}.crt"

if [ -e "$CAP_KEY" ]; then
  echo "$CAP_KEY already exists"
  exit 1
fi

openssl genrsa -out "${CAP_KEY}" 2048
openssl req -new -sha256 -key "${CAP_KEY}" -subj "/CN=$CAP" -out "${CAP_CERT}.csr" \
   -addext "keyUsage = digitalSignature, keyEncipherment, dataEncipherment"
openssl x509 -req -in "${CAP_CERT}.csr" -CA capsman-ca.crt -CAkey capsman-ca.key -out "${CAP_CERT}" -days 10000 -copy_extensions "copyall"
rm -f "${CAP_CERT}.csr"

#!/usr/bin/env bash
set -e
gpg --quiet --batch --yes --decrypt --passphrase="${BAHAMUT_PASSWORD}" bl.sfc.gz.gpg | gunzip > bl.sfc
make

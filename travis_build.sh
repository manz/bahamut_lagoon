#!/usr/bin/env bash
set -e

openssl aes-256-cbc -in bl.sfc.gz.aes -d -pass pass:${BAHAMUT_PASSWORD} | gunzip > bl.sfc
./build.py

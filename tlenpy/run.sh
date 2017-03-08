#!/usr/bin/env bash

if [ ! -f /data/sra/$1.sra ]; then
    echo "sra file not found!"
    ls /tlenpy
    python /tlenpy/get_srr.py $1 --base=/data
fi

cd /data/list

if [ ! -f /data/list/$1.list_25.list ]; then
    if [ ! -f /data/fastq/$1.fastq ]; then
        echo "Fastq not found, generating."
        fastq-dump /data/sra/$1.sra -O /data/fastq
    fi
    echo "List not found, generating."
    glistmaker /data/fastq/$1.fastq -w 25 -o $1.list -D
fi

echo "List found!"
glistquery $1.list_25.list -q TTAGGGTTAGGGTTAGGGTTAGGGT


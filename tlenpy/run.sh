#!/usr/bin/env bash

if [ ! -f /data/sra/$1.sra ]; then
    echo "File not found!"
    ls /tlenpy
    python /tlenpy/get_srr.py $1 --base=/data
fi

fastq-dump /data/sra/$1.sra -X 5 -O /data/fastq
cd /data/list
glistmaker /data/fastq/$1.fastq -w 25 -o $1.list
glistquery $1.list_25.list -all
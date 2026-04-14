#!/usr/bin/env -S python3 -u
import sys


for line in sys.stdin:
    key, _, _ = line.partition("\t")
    print(int(key))

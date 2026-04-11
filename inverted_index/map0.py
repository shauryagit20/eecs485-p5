#!/usr/bin/env -S python3 -u
"""Map 0."""

import sys

for line in sys.stdin:
    if line.startswith("<!DOCTYPE html>"):
        print(1)

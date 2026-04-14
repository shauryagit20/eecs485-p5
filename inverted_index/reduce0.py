#!/usr/bin/env -S python3 -u
"""Reduce 0."""

import sys

count = 0
for line in sys.stdin:
    stripped = line.strip()
    if stripped:
        count += int(stripped)

print(count)

#!/usr/bin/env python3
"""Fix syntax error in file_service.py"""
import os

file_path = os.path.join(os.path.dirname(__file__), '../../app/services/file_service.py')

with open(file_path, 'r') as f:
    lines = f.readlines()

# Fix line 302 by correcting the function signature
lines[301] = '                                access_level: str = "private") -> ClaimFile:\n'

with open(file_path, 'w') as f:
    f.writelines(lines)

print("Fixed syntax error in file_service.py")
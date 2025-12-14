#!/usr/bin/env python3
"""Fix encoding issues in crypto_moon_dashboard.py"""

# Read the file with error handling
with open('crypto_moon_dashboard.py', 'rb') as f:
    data = f.read()

# Remove problematic bytes
data = data.replace(b'\x9d', b'')
data = data.replace(b'\x8c', b'')

# Write back the cleaned file
with open('crypto_moon_dashboard.py', 'wb') as f:
    f.write(data)

print("✅ Fixed encoding issues in crypto_moon_dashboard.py")
# This script counts the number of lines in a specified text file.

import sys

if len(sys.argv) != 2:
    print("Usage: python count_lines.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

try:
    with open(filename, 'r') as file:
        line_count = sum(1 for line in file)
    print(f'Number of lines in {filename}: {line_count}')
except FileNotFoundError:
    print(f'Error: File {filename} not found.')
    sys.exit(1)
#! /usr/bin/env python3
'''
Functions/classes that are generally useful
'''
from gzip import open as gopen
from os.path import isfile
from sys import stdout

# useful constants
ASCII_MIN = 32
ASCII_MAX = 126

# load data from file
def load_data(data):
    if isinstance(data, bytes):
        return data
    elif isinstance(data, str) and isfile(data):
        if data.lower().endswith('.gz'):
            return gopen(data).read()
        else:
            return open(data, 'rb').read()
    else:
        raise ValueError("Invalid data argument: %s" % data)

# convert ASCII-containing bytes to string
def bytes_to_str(data):
    return ''.join(chr(v) for v in data if ASCII_MIN <= v <= ASCII_MAX)

# print bytes as hexadecimal numbers
def print_hex(data, delim=' ', end='\n', cols=16, f=stdout):
    for i, v in enumerate(data):
        if i != 0:
            if cols is not None and i % cols == 0:
                f.write(end)
            else:
                f.write(delim)
        f.write(hex(v)[2:].upper().zfill(2))
    f.write(end)

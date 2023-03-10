#! /usr/bin/env python3
'''
Functions/classes that are generally useful
'''
from gzip import open as gopen
from os.path import isdir, isfile
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

# save data to file
def save_data(data, out_file, overwrite=False):
    close_file = False
    if isinstance(out_file, str):
        if isfile(out_file) and not overwrite:
            raise ValueError("Output file exists: %s" % out_file)
        elif isdir(out_file):
            raise ValueError("Output exists as directory: %s" % out_file)
        if out_file.lower().endswith('.gz'):
            out_file = gopen(out_file, 'wb')
        else:
            out_file = open(out_file, 'wb')
        close_file = True
    out_file.write(data)
    if close_file:
        out_file.close()

# convert ASCII-containing bytes to string
def bytes_to_str(data):
    return ''.join(chr(v) for v in data if ASCII_MIN <= v <= ASCII_MAX)

# convert byte to hex string
def byte_to_hex_str(b, length=None):
    tmp = hex(b)[2:].upper()
    if length is None:
        return tmp
    else:
        return tmp.zfill(length)

# print bytes as hexadecimal numbers
def print_hex(data, delim=' ', end='\n', cols=16, f=stdout):
    for i, v in enumerate(data):
        if i != 0:
            if cols is not None and i % cols == 0:
                f.write(end)
            else:
                f.write(delim)
        f.write(byte_to_hex_str(v, length=2))
    f.write(end)

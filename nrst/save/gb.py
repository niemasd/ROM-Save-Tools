#! /usr/bin/env python3
'''
Nintendo GameBoy RAM Save Files (.sav)
'''
# Sources:
# http://gameboy.mongenel.com/dmg/asmmemmap.html
# https://gbdev.io/pandocs/Memory_Map.html
from .. import common
from struct import unpack
from sys import stdout

# GB memory map as (START, END, LABEL) tuples
MEMORY_MAP = [
    (0x0000, 0x7FFF, 'ROM Banks'), # see nrst.rom.gb.ROM_MEMORY_MAP
    (0x8000, 0x9FFF, 'Video RAM (VRAM)'),
    (0xA000, 0xBFFF, 'External RAM'),
    (0xC000, 0xCFFF, 'Work RAM (WRAM)'),
    (0xD000, 0xDFFF, 'Work RAM (WRAM)'),
    (0xE000, 0xFDFF, 'ECHO RAM (mirror of [0xC000, 0xDDFF])'),
    (0xFE00, 0xFE9F, 'Sprite Attribute Table (OAM)'), # https://gbdev.io/pandocs/OAM.html#vram-sprite-attribute-table-oam
    (0xFEA0, 0xFEFF, 'Not Usable'),
    (0xFF00, 0xFF7F, 'I/O Registers'), # https://gbdev.io/pandocs/Memory_Map.html#io-ranges
    (0xFF80, 0xFFFE, 'High RAM (HRAM)'),
    (0xFFFF, 0xFFFF, 'Interrupt Enable (IE) Register'), # https://gbdev.io/pandocs/Interrupts.html#interrupts
]


# helper class to represent GB RAM Saves (.sav)
class SAV:
    # initialize SAV object
    def __init__(self, data):
        self.data = common.load_data(data)

    # save SAV file
    def save(self, out_file, overwrite=False):
        common.save_data(self.data, out_file, overwrite=overwrite)

    # show a summary of this SAV
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Save Size: %d bytes%s" % (len(self.data), end))

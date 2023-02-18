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
    (0xFE00, 0xFE9F, 'Sprite Attribute Table (Object Attribute Memory, OAM)'), # https://gbdev.io/pandocs/OAM.html#vram-sprite-attribute-table-oam
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

    # get video RAM (VRAM)
    def get_vram(self):
        return self.data[0x8000:0xA000]

    # get external RAM
    def get_ext_ram(self):
        return self.data[0xA000:0xC000]

    # get work RAM (WRAM) 1
    def get_wram_1(self):
        return self.data[0xC000:0xD000]

    # get work RAM (WRAM) 2
    def get_wram_2(self):
        return self.data[0xD000:0xE000]

    # get ECHO RAM (should be mirror of [0xC000, 0xDDFF])
    def get_echo_ram(self):
        return self.data[0xE000:0xFE00]

    # get sprite attribute table (object attribute memory, OAM)
    def get_oam(self):
        return self.data[0xFE00:0xFEA0]

    # get I/O registers
    def get_io_reg(self):
        return self.data[0xFF00:0xFF80]

    # get high RAM (HRAM)
    def get_hram(self):
        return self.data[0xFF80:0xFFFF]

    # get interrupt enable (IE) register
    def get_ie_reg(self):
        return self.data[0xFFFF]

    # show a summary of this SAV
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Save Size: %d bytes%s" % (len(self.data), end))
        f.write("- ECHO RAM: %s%s" % ({True:'Valid',False:'Invalid'}[self.get_echo_ram() == self.data[0xC000:0xDE00]], end))

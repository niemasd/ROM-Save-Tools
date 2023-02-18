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
    (0x8000, 0x97FF, 'Video RAM (VRAM) - Tile Data'),
    (0x9800, 0x9BFF, 'Video RAM (VRAM) - Tile Map 1'),
    (0x9C00, 0x9FFF, 'Video RAM (VRAM) - Tile Map 2'),
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

# LCD control (LCDC) register bits as (MASK, LABEL, USAGE) tuples
LCDC_BITS = [
    (0b00000001, "BG and Window enable/priority", {0:'Off',           1:'On'}), # bit 0 (LSB)
    (0b00000010, "OBJ enable",                    {0:'Off',           1:'On'}),
    (0b00000100, "OBJ size",                      {0:'8x8',           1:'8x16'}),
    (0b00001000, "BG tile map area",              {0:(0x9800,0x9BFF), 1:(0x9C00,0x9FFF)}),
    (0b00010000, "BG and Window tile data area",  {0:(0x8800,0x97FF), 1:(0x8000,0x8FFF)}),
    (0b00100000, "Window enable",                 {0:'Off',           1:'On'}),
    (0b01000000, "Window tile map area",          {0:(0x9800,0x9BFF), 1:(0x9C00,0x9FFF)}),
    (0b10000000, "LCD and PPU enable",            {0:'Off',           1:'On'}), # bit 7 (MSB)
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
        return self.data[0x0000:0x2000] # [0x8000, 0xA000) - 0x8000

    # get external RAM
    def get_ext_ram(self):
        return self.data[0x2000:0x4000] # [0xA000, 0xC000) - 0x8000

    # get work RAM (WRAM) 1
    def get_wram_1(self):
        return self.data[0x4000:0x5000] # [0xC000, 0xD000) - 0x8000

    # get work RAM (WRAM) 2
    def get_wram_2(self):
        return self.data[0x5000:0x6000] # [0xD000, 0xE000) - 0x8000

    # get ECHO RAM (should be mirror of [0xC000, 0xDDFF])
    def get_echo_ram(self):
        return self.data[0x6000:0x7E00] # [0xE000, 0xFE00) - 0x8000

    # get sprite attribute table (object attribute memory, OAM)
    def get_oam(self):
        return self.data[0x7E00:0x7EA0] # [0xFE00, 0xFEA0) - 0x8000

    # get I/O registers
    def get_io_reg(self):
        return self.data[0x7F00:0x7F80] # [0xFF00, 0xFF80) - 0x8000

    # get high RAM (HRAM)
    def get_hram(self):
        return self.data[0x7F80:0x7FFF] # [0xFF80, 0xFFFF) - 0x8000

    # get interrupt enable (IE) register
    def get_ie_reg(self):
        return self.data[0x7FFF] # 0xFFFF - 0x8000

    # get LCD control (LCDC) register
    def get_lcdc(self):
        return self.data[0x7F40] # 0xFF40 - 0x8000

    # show a summary of this SAV
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Save Size: %d bytes%s" % (len(self.data), end))
        f.write("- ECHO RAM: %s%s" % ({True:'Valid',False:'Invalid'}[self.get_echo_ram() == self.data[0x4000:0x5E00]], end))
        lcdc = self.get_lcdc()
        f.write("- LCD Control (LCDC) Register: %s%s" % (bin(lcdc)[2:], end))
        for m, l, u in LCDC_BITS[::-1]: # print from bit 7 to bit 0
            v = u[(lcdc & m) % 1]
            if isinstance(v, tuple):
                v = "0x%s-0x%s" % (common.byte_to_hex_str(v[0]), common.byte_to_hex_str(v[1]))
            f.write("  - %s: %s%s" % (l, v, end))

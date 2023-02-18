#! /usr/bin/env python3
'''
Nintendo GameBoy Advance ROM Files (.gba)
'''
# Sources:
# http://problemkaputt.de/gbatek-gba-cartridge-header.htm
# https://github.com/devkitPro/gba-tools/blob/master/src/gbafix.c
from .. import common
from sys import stdout

# GBA ROM/cartridge memory map as (START, END, LABEL) tuples
ROM_MEMORY_MAP = [
    (0x0000, 0x0003, 'Header - Entry Point'),
    (0x0004, 0x009F, 'Header - Nintendo Logo'),
    (0x00A0, 0x00AB, 'Header - Title'),
    (0x00AC, 0x00AF, 'Header - Game Code'),
    (0x00B0, 0x00B1, 'Header - Licensee Code'),
    (0x00B2, 0x00B2, 'Header - Fixed Value (0x96)'),
    (0x00B3, 0x00B3, 'Header - Main Unit Code (0x00)'),
    (0x00B4, 0x00B4, 'Header - Device Type (0x00)'),
    (0x00B5, 0x00BB, 'Header - Reserved Area (0x00 * 7)'),
    (0x00BC, 0x00BC, 'Header - ROM Version Number'),
    (0x00BD, 0x00BD, 'Header - Checksum of [0x00A0, 0x00BC]'),
    (0x00BE, 0x00BF, 'Header - Reserved Area (0x00 * 2)'),
    (0x00C0, 0x00C3, 'Multiboot Header - RAM Entry Point'),
    (0x00C4, 0x00C4, 'Multiboot Header - Boot Mode (0x00)'),
    (0x00C5, 0x00C5, 'Multiboot Header - Slave ID Number (0x00)'),
    (0x00C6, 0x00DF, 'Multiboot Header - Unused'),
    (0x00E0, 0x00E3, 'Multiboot Header - JOYBUS Entry Point'),
]

NINTENDO_LOGO = bytes([0x24, 0xFF, 0xAE, 0x51, 0x69, 0x9A, 0xA2, 0x21, 0x3D, 0x84, 0x82, 0x0A, 0x84, 0xE4, 0x09, 0xAD, 0x11, 0x24, 0x8B, 0x98, 0xC0, 0x81, 0x7F, 0x21, 0xA3, 0x52, 0xBE, 0x19, 0x93, 0x09, 0xCE, 0x20, 0x10, 0x46, 0x4A, 0x4A, 0xF8, 0x27, 0x31, 0xEC, 0x58, 0xC7, 0xE8, 0x33, 0x82, 0xE3, 0xCE, 0xBF, 0x85, 0xF4, 0xDF, 0x94, 0xCE, 0x4B, 0x09, 0xC1, 0x94, 0x56, 0x8A, 0xC0, 0x13, 0x72, 0xA7, 0xFC, 0x9F, 0x84, 0x4D, 0x73, 0xA3, 0xCA, 0x9A, 0x61, 0x58, 0x97, 0xA3, 0x27, 0xFC, 0x03, 0x98, 0x76, 0x23, 0x1D, 0xC7, 0x61, 0x03, 0x04, 0xAE, 0x56, 0xBF, 0x38, 0x84, 0x00, 0x40, 0xA7, 0x0E, 0xFD, 0xFF, 0x52, 0xFE, 0x03, 0x6F, 0x95, 0x30, 0xF1, 0x97, 0xFB, 0xC0, 0x85, 0x60, 0xD6, 0x80, 0x25, 0xA9, 0x63, 0xBE, 0x03, 0x01, 0x4E, 0x38, 0xE2, 0xF9, 0xA2, 0x34, 0xFF, 0xBB, 0x3E, 0x03, 0x44, 0x78, 0x00, 0x90, 0xCB, 0x88, 0x11, 0x3A, 0x94, 0x65, 0xC0, 0x7C, 0x63, 0x87, 0xF0, 0x3C, 0xAF, 0xD6, 0x25, 0xE4, 0x8B, 0x38, 0x0A, 0xAC, 0x72, 0x21, 0xD4, 0xF8, 0x07])

# GBA game code [0x00AC, 0x00B0) first letter
GAME_CODE_0 = {
    'A': 'Normal Game, Older (mainly 2001-2003)',
    'B': 'Normal Game, Newer (mainly 2003+)',
    'C': 'Normal Game, Unused',
    'F': 'Famicom/Classic NES Series (software-emulated NES games)',
    'K': 'Yoshi and Koro Koro Puzzle (acceleration sensor)',
    'P': 'e-Reader (dot-code scanner) or NDS PassMe image when gamecode="PASS"',
    'R': 'Warioware Twisted (cartridge with rumble and z-axis gyro sensor)',
    'U': 'Boktai 1 and 2 (cartridge with RTC and solar sensor)',
    'V': 'Drill Dozer (cartridge with rumble)',
}

# GBA game code [0x00AC, 0x00B0) last letter (destination/language)
GAME_CODE_3 = {
    'D': 'German',
    'E': 'USA/English',
    'F': 'French',
    'I': 'Italian',
    'J': 'Japanese',
    'P': 'Europe/Elsewhere',
    'S': 'Spanish',
}

# GBA licensee code (need to expand)
LICENSEE_CODES = {
    '01': 'Nintendo',
}

# helper class to represent GBA ROMs (.gba)
class GBA:
    # initialize GBA object
    def __init__(self, data):
        self.data = common.load_data(data)

    # save GBA file
    def save(self, out_file, overwrite=False):
        common.save_data(self.data, out_file, overwrite=overwrite)

    # get title
    def get_title(self):
        return common.bytes_to_str(self.data[0x00A0:0x00AC])

    # get game code
    def get_game_code(self):
        return ''.join(chr(v) for v in self.data[0x00AC:0x00B0])

    # get licensee
    def get_licensee(self):
        licensee_code = ''.join(chr(v) for v in self.data[0x00B0:0x00B2])
        if licensee_code in LICENSEE_CODES:
            return LICENSEE_CODES[licensee_code]
        else:
            return "Unknown"

    # get ROM version number
    def get_rom_version(self):
        return self.data[0x00BC]

    # get header checksum from 0x00BD
    def get_header_checksum(self):
        return self.data[0x00BD]

    # calculate header checksum from bytes in [0x00A0, 0x00BC], which should equal 0x00BD
    def calc_header_checksum(self):
        checksum = 256
        for i in range(0x00A0, 0x00BD):
            checksum -= self.data[i]
            while checksum < 0:
                checksum += 256
        checksum -= 0x19
        while checksum < 0:
            checksum += 256
        return checksum

    # show a summary of this ROM
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Cartridge Size: %d bytes%s" % (len(self.data), end))
        f.write("- Title: %s%s" % (self.get_title(), end))
        game_code = self.get_game_code()
        f.write("- Game Code: %s%s" % (game_code, end))
        f.write("  - %s = %s%s" % (game_code[0], GAME_CODE_0[game_code[0]], end))
        f.write("  - %s = abbreviation of title%s" % (game_code[1:3], end))
        f.write("  - %s = %s%s" % (game_code[3], GAME_CODE_3[game_code[3]], end))
        f.write("- Licensee: %s%s" % (self.get_licensee(), end))
        f.write("- ROM Version: %d%s" % (self.get_rom_version(), end))
        f.write("- Header Checksum (from ROM header): %d%s" % (self.get_header_checksum(), end))
        f.write("- Header Checksum (calculated): %d%s" % (self.calc_header_checksum(), end))

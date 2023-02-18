#! /usr/bin/env python3
'''
Nintendo GameBoy ROM Files (.gb) and GameBoy Color ROM Files (.gbc)
'''
# Sources:
# http://gameboy.mongenel.com/dmg/asmmemmap.html
# https://gbdev.io/pandocs/The_Cartridge_Header.html
from .. import common
from struct import unpack
from sys import stdout

# GB ROM/cartridge memory map as (START, END, LABEL) tuples
ROM_MEMORY_MAP = [
    (0x0000, 0x00FF, 'Restart and Interrupt Vector Table'),
    (0x0100, 0x0103, 'Header - Entry Point'),
    (0x0104, 0x0133, 'Header - Nintendo Logo'),
    (0x0134, 0x013E, 'Header - Title'),
    (0x013F, 0x0142, 'Header - Manufacturer Code (or Title continued)'),
    (0x0143, 0x0143, 'Header - CGB Flag (or Title continued)'),
    (0x0144, 0x0145, 'Header - New Licensee Code'),
    (0x0146, 0x0146, 'Header - SGB Flag'),
    (0x0147, 0x0147, 'Header - Cartridge Type'),
    (0x0148, 0x0148, 'Header - ROM Banks'),
    (0x0149, 0x0149, 'Header - RAM Banks'),
    (0x014A, 0x014A, 'Header - Destination Code'),
    (0x014B, 0x014B, 'Header - Old Licensee Code'),
    (0x014C, 0x014C, 'Header - ROM Version Number'),
    (0x014D, 0x014D, 'Header - Checksum of [0x0134, 0x014C]'),
    (0x014E, 0x014F, 'Header - Checksum of Entire Cartridge'),
    (0x0150, 0x3FFF, 'Cartridge ROM - Bank 0'),
    (0x4000, 0x7FFF, 'Cartridge ROM - Switchable Banks 1+'),
]

NINTENDO_LOGO = bytes([0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D, 0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99, 0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E])

# GB new licensee codes (0x0144-0x0145)
NEW_LICENSEE_CODES = {
    '00': "None",
    '01': "Nintendo R&D1",
    '08': "Capcom",
    '13': "Electronic Arts",
    '18': "Hudson Soft",
    '19': "b-ai",
    '20': "kss",
    '22': "pow",
    '24': "PCM Complete",
    '25': "san-x",
    '28': "Kemco Japan",
    '29': "seta",
    '30': "Viacom",
    '31': "Nintendo",
    '32': "Bandai",
    '33': "Ocean/Acclaim",
    '34': "Konami",
    '35': "Hector",
    '37': "Taito",
    '38': "Hudson",
    '39': "Banpresto",
    '41': "Ubi Soft",
    '42': "Atlus",
    '44': "Malibu",
    '46': "angel",
    '47': "Bullet-Proof",
    '49': "irem",
    '50': "Absolute",
    '51': "Acclaim",
    '52': "Activision",
    '53': "American sammy",
    '54': "Konami",
    '55': "Hi tech entertainment",
    '56': "LJN",
    '57': "Matchbox",
    '58': "Mattel",
    '59': "Milton Bradley",
    '60': "Titus",
    '61': "Virgin",
    '64': "LucasArts",
    '67': "Ocean",
    '69': "Electronic Arts",
    '70': "Infogrames",
    '71': "Interplay",
    '72': "Broderbund",
    '73': "sculptured",
    '75': "sci",
    '78': "THQ",
    '79': "Accolade",
    '80': "misawa",
    '83': "lozc",
    '86': "Tokuma Shoten Intermedia",
    '87': "Tsukuda Original",
    '91': "Chunsoft",
    '92': "Video system",
    '93': "Ocean/Acclaim",
    '95': "Varie",
    '96': "Yonezawa/s'pal",
    '97': "Kaneko",
    '99': "Pack in soft",
    'A4': "Konami (Yu-Gi-Oh!)",
}

# GB catridge types (0x0147)
CARTRIDGE_TYPES = {
    0x00: 'ROM ONLY',
    0x01: 'MBC1',
    0x02: 'MBC1+RAM',
    0x03: 'MBC1+RAM+BATTERY',
    0x05: 'MBC2',
    0x06: 'MBC2+BATTERY',
    0x08: 'ROM+RAM',
    0x09: 'ROM+RAM+BATTERY',
    0x0B: 'MMM01',
    0x0C: 'MMM01+RAM',
    0x0D: 'MMM01+RAM+BATTERY',
    0x0F: 'MBC3+TIMER+BATTERY',
    0x10: 'MBC3+TIMER+RAM+BATTERY',
    0x11: 'MBC3',
    0x12: 'MBC3+RAM',
    0x13: 'MBC3+RAM+BATTERY',
    0x19: 'MBC5',
    0x1A: 'MBC5+RAM',
    0x1B: 'MBC5+RAM+BATTERY',
    0x1C: 'MBC5+RUMBLE',
    0x1D: 'MBC5+RUMBLE+RAM',
    0x1E: 'MBC5+RUMBLE+RAM+BATTERY',
    0x20: 'MBC6',
    0x22: 'MBC7+SENSOR+RUMBLE+RAM+BATTERY',
    0xFC: 'POCKET CAMERA',
    0xFD: 'BANDAI TAMA5',
    0xFE: 'HuC3',
    0xFF: 'HuC1+RAM+BATTERY',
}

# GB ROM banks (0x0148) as (ROM size in bytes, number of banks) tuples
ROM_BANKS = {
    0x00: (  32768,   2),
    0x01: (  65536,   4),
    0x02: ( 131072,   8),
    0x03: ( 262144,  16),
    0x04: ( 524288,  32),
    0x05: (1048576,  64),
    0x06: (2097152, 128),
    0x07: (4194304, 256),
    0x08: (8388608, 512),
    0x52: (1179648,  72), # no known ROMs use this
    0x53: (1310720,  80), # no known ROMs use this
    0x54: (1572864,  96), # no known ROMs use this
}

# GB RAM banks (0x0149) as (SRAM size in bytes, number of banks) tuples
RAM_BANKS = {
    0x00: (     0,  0),
    0x01: (  2048,  1), # used in some PD homebrew ROMs, but size is actually (usually?) 0 in those cases
    0x02: (  8192,  1),
    0x03: ( 32768,  4),
    0x04: (131072, 16),
    0x05: ( 65536,  8),
}

# GB destination codes (0x014A)
DESTINATION_CODES = {
    0x00: "Japan (and possibly overseas)",
    0x01: "Overseas only",
}

# GB old licensee codes (0x014B)
OLD_LICENSEE_CODES = {
    0x00: "None",
    0x01: "Nintendo",
    0x08: "Capcom",
    0x09: "Hot-B",
    0x0A: "Jaleco",
    0x0B: "Coconuts Japan",
    0x0C: "Elite Systems",
    0x13: "EA (Electronic Arts)",
    0x18: "Hudsonsoft",
    0x19: "ITC Entertainment",
    0x1A: "Yanoman",
    0x1D: "Japan Clary",
    0x1F: "Virgin Interactive",
    0x24: "PCM Complete",
    0x25: "San-X",
    0x28: "Kotobuki Systems",
    0x29: "Seta",
    0x30: "Infogrames",
    0x31: "Nintendo",
    0x32: "Bandai",
    0x33: None, # use new licensee code instead
    0x34: "Konami",
    0x35: "HectorSoft",
    0x38: "Capcom",
    0x39: "Banpresto",
    0x3C: ".Entertainment i",
    0x3E: "Gremlin",
    0x41: "Ubisoft",
    0x42: "Atlus",
    0x44: "Malibu",
    0x46: "Angel",
    0x47: "Spectrum Holoby",
    0x49: "Irem",
    0x4A: "Virgin Interactive",
    0x4D: "Malibu",
    0x4F: "U.S. Gold",
    0x50: "Absolute",
    0x51: "Acclaim",
    0x52: "Activision",
    0x53: "American Sammy",
    0x54: "GameTek",
    0x55: "Park Place",
    0x56: "LJN",
    0x57: "Matchbox",
    0x59: "Milton Bradley",
    0x5A: "Mindscape",
    0x5B: "Romstar",
    0x5C: "Naxat Soft",
    0x5D: "Tradewest",
    0x60: "Titus",
    0x61: "Virgin Interactive",
    0x67: "Ocean Interactive",
    0x69: "EA (Electronic Arts)",
    0x6E: "Elite Systems",
    0x6F: "Electro Brain",
    0x70: "Infogrames",
    0x71: "Interplay",
    0x72: "Broderbund",
    0x73: "Sculptered Soft",
    0x75: "The Sales Curve",
    0x78: "t.hq",
    0x79: "Accolade",
    0x7A: "Triffix Entertainment",
    0x7C: "Microprose",
    0x7F: "Kemco",
    0x80: "Misawa Entertainment",
    0x83: "Lozc",
    0x86: "Tokuma Shoten Intermedia",
    0x8B: "Bullet-Proof Software",
    0x8C: "Vic Tokai",
    0x8E: "Ape",
    0x8F: "I'Max",
    0x91: "Chunsoft Co.",
    0x92: "Video System",
    0x93: "Tsubaraya Productions Co.",
    0x95: "Varie Corporation",
    0x96: "Yonezawa/S'Pal",
    0x97: "Kaneko",
    0x99: "Arc",
    0x9A: "Nihon Bussan",
    0x9B: "Tecmo",
    0x9C: "Imagineer",
    0x9D: "Banpresto",
    0x9F: "Nova",
    0xA1: "Hori Electric",
    0xA2: "Bandai",
    0xA4: "Konami",
    0xA6: "Kawada",
    0xA7: "Takara",
    0xA9: "Technos Japan",
    0xAA: "Broderbund",
    0xAC: "Toei Animation",
    0xAD: "Toho",
    0xAF: "Namco",
    0xB0: "acclaim",
    0xB1: "ASCII or Nexsoft",
    0xB2: "Bandai",
    0xB4: "Square Enix",
    0xB6: "HAL Laboratory",
    0xB7: "SNK",
    0xB9: "Pony Canyon",
    0xBA: "Culture Brain",
    0xBB: "Sunsoft",
    0xBD: "Sony Imagesoft",
    0xBF: "Sammy",
    0xC0: "Taito",
    0xC2: "Kemco",
    0xC3: "Squaresoft",
    0xC4: "Tokuma Shoten Intermedia",
    0xC5: "Data East",
    0xC6: "Tonkinhouse",
    0xC8: "Koei",
    0xC9: "UFL",
    0xCA: "Ultra",
    0xCB: "Vap",
    0xCC: "Use Corporation",
    0xCD: "Meldac",
    0xCE: ".Pony Canyon or",
    0xCF: "Angel",
    0xD0: "Taito",
    0xD1: "Sofel",
    0xD2: "Quest",
    0xD3: "Sigma Enterprises",
    0xD4: "ASK Kodansha Co.",
    0xD6: "Naxat Soft",
    0xD7: "Copya System",
    0xD9: "Banpresto",
    0xDA: "Tomy",
    0xDB: "LJN",
    0xDD: "NCS",
    0xDE: "Human",
    0xDF: "Altron",
    0xE0: "Jaleco",
    0xE1: "Towa Chiki",
    0xE2: "Yutaka",
    0xE3: "Varie",
    0xE5: "Epcoh",
    0xE7: "Athena",
    0xE8: "Asmik ACE Entertainment",
    0xE9: "Natsume",
    0xEA: "King Records",
    0xEB: "Atlus",
    0xEC: "Epic/Sony Records",
    0xEE: "IGS",
    0xF0: "A Wave",
    0xF3: "Extreme Entertainment",
    0xFF: "LJN",
}

# helper class to represent GB ROMs (.gb) and GBC ROMs (.gbc)
class GB:
    # initialize GB object
    def __init__(self, data):
        self.data = common.load_data(data)

    # save GB file
    def save(self, out_file, overwrite=False):
        common.save_data(self.data, out_file, overwrite=overwrite)

    # get title (might include manufacturer code)
    def get_title(self):
        if self.get_manufacturer_code() is None:
            return common.bytes_to_str(self.data[0x0134:0x0144])
        else:
            return common.bytes_to_str(self.data[0x0134:0x013F])

    # get manufacturer code (might just be part of title)
    def get_manufacturer_code(self):
        tmp = common.bytes_to_str(self.data[0x013F:0x0143])
        if len(tmp) != 4 or sum('A' <= c <= 'Z' for c in tmp) != 4:
            return None
        return tmp

    # check CGB flag
    def check_cgb(self):
        cgb_flag = self.data[0x0143]
        if cgb_flag == 0x80:
            return "CGB Mode"
        elif cgb_flag == 0xC0:
            return "Non-CGB Mode"
        elif (cgb_flag & 0b00001100) != 0:
            return "PGB Mode"
        else:
            return None # probably old GB game where this byte is part of title

    # check SGB flag
    def check_sgb(self):
        sgb_flag = self.data[0x0146]
        return sgb_flag == 0x03

    # get cartridge type
    def get_cartridge_type(self):
        tmp = self.data[0x0147]
        if tmp not in CARTRIDGE_TYPES:
            raise ValueError("Invalid cartridge type: %s" % common.byte_to_hex_str(tmp))
        return CARTRIDGE_TYPES[tmp]

    # get ROM size and number of ROM banks as (size in bytes, number of banks) tuple
    def get_rom_size_num_banks(self):
        tmp = self.data[0x0148]
        if tmp not in ROM_BANKS:
            raise ValueError("Invalid ROM size: %s" % common.byte_to_hex_str(tmp))
        return ROM_BANKS[tmp]

    # get RAM size and banks as (SRAM size in bytes, number of banks) tuple
    def get_ram_size_num_banks(self):
        tmp = self.data[0x0149]
        if tmp not in RAM_BANKS:
            raise ValueError("Invalid RAM size: %s" % common.byte_to_hex_str(tmp))
        return RAM_BANKS[tmp]

    # get destination
    def get_destination(self):
        tmp = self.data[0x014A]
        if tmp not in DESTINATION_CODES:
            raise ValueError("Invalid destination code: %s" % common.byte_to_hex_str(tmp))
        return DESTINATION_CODES[tmp]

    # get licensee
    def get_licensee(self):
        old_code = self.data[0x014B]
        if old_code == 0x33: # use new code instead
            new_code = ''.join(chr(v) for v in self.data[0x0144:0x0146])
            if new_code not in NEW_LICENSEE_CODES:
                raise ValueError("Invalid new licensee code: %s" % new_code)
            return NEW_LICENSEE_CODES[new_code]
        elif old_code not in OLD_LICENSEE_CODES:
            raise ValueError("Invalid old licensee code: %s" % common.byte_to_hex_str(old_code))
        return OLD_LICENSEE_CODES[old_code]

    # get ROM version number
    def get_rom_version(self):
        return self.data[0x014C]

    # get header checksum from 0x014D
    def get_header_checksum(self):
        return self.data[0x014D]

    # calculate header checksum from bytes in [0x0134, 0x014C], which should equal 0x014D
    def calc_header_checksum(self):
        checksum = 256
        for i in range(0x0134, 0x014D):
            checksum -= (self.data[i]+1)
            while checksum < 0:
                checksum += 256
        return checksum

    # get global checksum from [0x014E, 0x0150), which is a 16-bit big-endian integer
    def get_global_checksum(self):
        return unpack('>H', self.data[0x014E:0x0150])[0]

    # calculate global checksum, which should be equal to [0x014E, 0x0150)
    def calc_global_checksum(self):
        return sum(v for i,v in enumerate(self.data) if i != 0x014E and i != 0x014F) % 65536

    # show a summary of this ROM
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Cartridge Size: %d bytes%s" % (len(self.data), end))
        f.write("- Title: %s%s" % (self.get_title(), end))
        manufacturer_code = self.get_manufacturer_code()
        if manufacturer_code is not None:
            f.write("- Manufacturer Code: %s%s" % (manufacturer_code, end))
        cgb = self.check_cgb()
        if cgb is not None:
            f.write("- CGB Flag: %s%s" % (cgb, end))
        f.write("- SGB Flag: %s%s" % (self.check_sgb(), end))
        f.write("- Cartridge Type: %s%s" % (self.get_cartridge_type(), end))
        rom_bank_size, num_rom_banks = self.get_rom_size_num_banks()
        f.write("- ROM Bank Size: %d bytes%s" % (rom_bank_size, end))
        f.write("- Number of ROM Banks: %d%s" % (num_rom_banks, end))
        sram_size, num_ram_banks = self.get_ram_size_num_banks()
        f.write("- SRAM Size: %d bytes%s" % (sram_size, end))
        f.write("- Number of RAM Banks: %d%s" % (num_ram_banks, end))
        f.write("- Destination: %s%s" % (self.get_destination(), end))
        f.write("- Licensee: %s%s" % (self.get_licensee(), end))
        f.write("- ROM Version: %d%s" % (self.get_rom_version(), end))
        f.write("- Header Checksum (from ROM header): %d%s" % (self.get_header_checksum(), end))
        f.write("- Header Checksum (calculated): %d%s" % (self.calc_header_checksum(), end))
        f.write("- Global Checksum (from ROM header): %d%s" % (self.get_global_checksum(), end))
        f.write("- Global Checksum (calculated): %d%s" % (self.calc_global_checksum(), end))

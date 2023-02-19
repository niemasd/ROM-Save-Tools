#! /usr/bin/env python3
'''
Nintendo GameBoy Advance Save Files
'''
from .. import common
from gzip import open as gopen
from os.path import isdir, isfile
from struct import pack, unpack
from sys import stdout

# VBA SGM save game struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L342-L459
VBA_SGM_SAVE_GAME_STRUCT = [
    ('DISPCNT',              2, '<H'),
    ('DISPSTAT',             2, '<H'),
    ('VCOUNT',               2, '<H'),
    ('BG0CNT',               2, '<H'),
    ('BG1CNT',               2, '<H'),
    ('BG2CNT',               2, '<H'),
    ('BG3CNT',               2, '<H'),
    ('BG0HOFS',              2, '<H'),
    ('BG0VOFS',              2, '<H'),
    ('BG1HOFS',              2, '<H'),
    ('BG1VOFS',              2, '<H'),
    ('BG2HOFS',              2, '<H'),
    ('BG2VOFS',              2, '<H'),
    ('BG3HOFS',              2, '<H'),
    ('BG3VOFS',              2, '<H'),
    ('BG2PA',                2, '<H'),
    ('BG2PB',                2, '<H'),
    ('BG2PC',                2, '<H'),
    ('BG2PD',                2, '<H'),
    ('BG2X_L',               2, '<H'),
    ('BG2X_H',               2, '<H'),
    ('BG2Y_L',               2, '<H'),
    ('BG2Y_H',               2, '<H'),
    ('BG3PA',                2, '<H'),
    ('BG3PB',                2, '<H'),
    ('BG3PC',                2, '<H'),
    ('BG3PD',                2, '<H'),
    ('BG3X_L',               2, '<H'),
    ('BG3X_H',               2, '<H'),
    ('BG3Y_L',               2, '<H'),
    ('BG3Y_H',               2, '<H'),
    ('WIN0H',                2, '<H'),
    ('WIN1H',                2, '<H'),
    ('WIN0V',                2, '<H'),
    ('WIN1V',                2, '<H'),
    ('WININ',                2, '<H'),
    ('WINOUT',               2, '<H'),
    ('MOSAIC',               2, '<H'),
    ('BLDMOD',               2, '<H'),
    ('COLEV',                2, '<H'),
    ('COLY',                 2, '<H'),
    ('DM0SAD_L',             2, '<H'),
    ('DM0SAD_H',             2, '<H'),
    ('DM0DAD_L',             2, '<H'),
    ('DM0DAD_H',             2, '<H'),
    ('DM0CNT_L',             2, '<H'),
    ('DM0CNT_H',             2, '<H'),
    ('DM1SAD_L',             2, '<H'),
    ('DM1SAD_H',             2, '<H'),
    ('DM1DAD_L',             2, '<H'),
    ('DM1DAD_H',             2, '<H'),
    ('DM1CNT_L',             2, '<H'),
    ('DM1CNT_H',             2, '<H'),
    ('DM2SAD_L',             2, '<H'),
    ('DM2SAD_H',             2, '<H'),
    ('DM2DAD_L',             2, '<H'),
    ('DM2DAD_H',             2, '<H'),
    ('DM2CNT_L',             2, '<H'),
    ('DM2CNT_H',             2, '<H'),
    ('DM3SAD_L',             2, '<H'),
    ('DM3SAD_H',             2, '<H'),
    ('DM3DAD_L',             2, '<H'),
    ('DM3DAD_H',             2, '<H'),
    ('DM3CNT_L',             2, '<H'),
    ('DM3CNT_H',             2, '<H'),
    ('TM0D',                 2, '<H'),
    ('TM0CNT',               2, '<H'),
    ('TM1D',                 2, '<H'),
    ('TM1CNT',               2, '<H'),
    ('TM2D',                 2, '<H'),
    ('TM2CNT',               2, '<H'),
    ('TM3D',                 2, '<H'),
    ('TM3CNT',               2, '<H'),
    ('P1',                   2, '<H'),
    ('IE',                   2, '<H'),
    ('IF',                   2, '<H'),
    ('IME',                  2, '<H'),
    ('holdState',            1,  '?'),
    ('holdType',             4, '<i'),
    ('lcdTicks',             4, '<i'),
    ('timer0On',             1,  '?'),
    ('timer0Ticks',          4, '<i'),
    ('timer0Reload',         4, '<i'),
    ('timer0ClockReload',    4, '<i'),
    ('timer1On',             1,  '?'),
    ('timer1Ticks',          4, '<i'),
    ('timer1Reload',         4, '<i'),
    ('timer1ClockReload',    4, '<i'),
    ('timer2On',             1,  '?'),
    ('timer2Ticks',          4, '<i'),
    ('timer2Reload',         4, '<i'),
    ('timer2ClockReload',    4, '<i'),
    ('timer3On',             1,  '?'),
    ('timer3Ticks',          4, '<i'),
    ('timer3Reload',         4, '<i'),
    ('timer3ClockReload',    4, '<i'),
    ('dma0Source',           4, '<I'),
    ('dma0Dest',             4, '<I'),
    ('dma1Source',           4, '<I'),
    ('dma1Dest',             4, '<I'),
    ('dma2Source',           4, '<I'),
    ('dma2Dest',             4, '<I'),
    ('dma3Source',           4, '<I'),
    ('dma3Dest',             4, '<I'),
    ('fxOn',                 1,  '?'),
    ('windowOn',             1,  '?'),
    ('N_FLAG',               1,  '?'),
    ('C_FLAG',               1,  '?'),
    ('Z_FLAG',               1,  '?'),
    ('V_FLAG',               1,  '?'),
    ('armState',             1,  '?'),
    ('armIrqEnable',         1,  '?'),
    ('armNextPC',            4, '<I'),
    ('armMode',              4, '<i'),
    ('coreOptions.saveType', 4, '<i'),
]

# helper class to represent VisualBoyAdvance (VBA) save states (.sgm)
# CPUWriteState: https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L703-L738
# CPUReadState:  https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L776-L919
# utilWriteInt:  https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/Util.cpp#L723-L726
class VBA_SGM:
    # initialize VBA_SGM object
    def __init__(self, filename):
        data = gopen(filename).read(); ind = 0x0000
        self.save_game_version = unpack('<i', data[ind:ind+4])[0]; ind += 4 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L778-L785
        self.rom_name = common.bytes_to_str(data[ind:ind+16]); ind += 16 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L787-L798
        self.use_bios = False if unpack('<i', data[ind:ind+4])[0] == 0 else True; ind += 4 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L800-L810
        self.reg = list() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L812
        for _ in range(45):
            self.reg.append(data[ind:ind+4])
        self.save_game_struct = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L814
        for n, s, f in VBA_SGM_SAVE_GAME_STRUCT:
            self.save_game_struct[n] = unpack(f, data[ind:ind+s])[0]; ind += s
        if self.save_game_version < 3: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L816-L819
            self.stop_state = False
        else:
            self.stop_state = False if unpack('<i', data[ind:ind+4])[0] == 0 else True; ind += 4
        if self.save_game_version < 4: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L821-L832
            self.irq_tricks = 0
            self.int_state = False
        else:
            self.irq_tricks = unpack('<i', data[ind:ind+4])[0]
            if self.irq_tricks > 0:
                self.int_state = True
            else:
                self.irq_tricks = 0
                self.int_state = False
        # TODO HERE

    # save VBA_SGM file
    def save(self, filename, overwrite=False):
        if not filename.lower().endswith('.sgm'):
            raise ValueError("Output VGA SGM file extension must be '.sgm': %s" % filename)
        elif (isfile(filename) or isdir(filename)) and not overwrite:
            raise ValueError("Output file exists: %s" % filename)
        out = gopen(filename, 'wb')
        out.write(pack('<i', self.save_game_version))
        out.write(bytes([ord(c) for c in self.rom_name] + [0]*(16-len(self.rom_name))))
        out.write(pack('<i', {True:1,False:0}[self.use_bios]))
        for reg_chunk in self.reg:
            out.write(reg_chunk)
        for n, s, f in VBA_SGM_SAVE_GAME_STRUCT:
            out.write(pack(f, self.save_game_struct[n]))
        if self.save_game_version >= 3:
            out.write(pack('<i', {True:1,False:0}[self.stop_state]))
        if self.save_game_version >= 4:
            out.write(pack('<i', self.irq_tricks))
        # TODO HERE
        out.close()

    # show a summary of this VBA_SGM
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Save Game Version: %d%s" % (self.save_game_version, end))
        f.write("- ROM Name: %s%s" % (self.rom_name, end))
        f.write("- Use BIOS: %s%s" % (self.use_bios, end))
        f.write("- Size of reg: %d bytes%s" % (len(self.reg)*len(self.reg[0]), end))
        f.write("- Save Game Struct: %d items%s" % (len(self.save_game_struct), end))
        for n, _, __ in VBA_SGM_SAVE_GAME_STRUCT:
            f.write("  - %s: %s%s" % (n, self.save_game_struct[n], end))
        f.write("- Stop State: %s%s" % (self.stop_state, end))
        f.write("- IRQ Tricks: %d%s" % (self.irq_tricks, end))
        f.write("- Int State: %s%s" % (self.int_state, end))
        '''
        f.write("- Save Size: %d bytes%s" % (len(self.data), end))
        f.write("- ECHO RAM: %s%s" % ({True:'Valid',False:'Invalid'}[self.get_echo_ram() == self.data[0x4000:0x5E00]], end))
        lcdc = self.get_lcdc()
        f.write("- LCD Control (LCDC) Register: %s%s" % (bin(lcdc)[2:], end))
        for m, l, u in LCDC_BITS[::-1]: # print from bit 7 to bit 0
            v = u[{True:0,False:1}[(lcdc & m) == 0]]
            if isinstance(v, tuple):
                v = "0x%s-0x%s" % (common.byte_to_hex_str(v[0]), common.byte_to_hex_str(v[1]))
            f.write("  - %s: %s%s" % (l, v, end))
        '''

#! /usr/bin/env python3
'''
Nintendo GameBoy Advance Save Files
'''
from .. import common
from gzip import open as gopen
from struct import unpack
from sys import stdout



# helper class to represent VisualBoyAdvance (VBA) save states (.sgm)
# CPUWriteState: https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L703-L738
# CPUReadState:  https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L776-L919
# utilWriteInt:  https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/Util.cpp#L723-L726
class VBA_SGM:
    # initialize VBA_SGM object
    def __init__(self, filename):
        data = gopen(filename).read()
        self.save_game_version = unpack('<i', data[0x0000:0x0004])[0]

    # save VBA_SGM file
    def save(self, out_file, overwrite=False):
        pass # TODO
        #common.save_data(self.data, out_file, overwrite=overwrite)

    # show a summary of this VBA_SGM
    def show_summary(self, f=stdout, end='\n'):
        f.write("- Save Game Version: %d%s" % (self.save_game_version, end))
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

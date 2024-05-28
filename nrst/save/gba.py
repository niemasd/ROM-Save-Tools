#! /usr/bin/env python3
'''
Nintendo GameBoy Advance Save Files
'''
from .. import common
from gzip import open as gopen
from os.path import isdir, isfile
from struct import pack, unpack
from sys import stdout

# relevant GBA sizes
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/GBA.h#L34-L56
SIZE = {
    'SRAM':       0x0008000,
    'FLASH_512':  0x0010000,
    'FLASH_1M':   0x0020000,
    'EEPROM_512': 0x0000200,
    'EEPROM_8K':  0x0002000,
    'ROM':        0x2000000,
    'BIOS':       0x0004000,
    'IRAM':       0x0008000,
    'WRAM':       0x0040000,
    'PRAM':       0x0000400,
    'VRAM':       0x0020000,
    'OAM':        0x0000400,
    'IOMEM':      0x0000400,
    'PIX':        0x0025800, # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/GBA.h#L54
    'PIX_ALT':    0x0026208, # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/GBA.h#L52
}

# VBA constants
VBA_MAX_CHEATS = 16384

# VBA CheatsData struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Cheats.h#L6-L17
VBA_CHEATS_DATA_STRUCT = [
    ('code',        4, '<i'),
    ('size',        4, '<i'),
    ('status',      4, '<i'),
    ('enabled',     1,  '?'),
    ('rawaddress',  4, '<I'),
    ('address',     4, '<I'),
    ('value',       4, '<I'),
    ('oldValue',    4, '<I'),
    ('codestring', 20, None),
    ('desc',       32, None),
]

# VBA RTCCLOCKDATA struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/gba/RTC.cpp#L19-L33
VBA_RTC_CLOCK_DATA_STRUCT = [
    ('byte0',     1,  'B'),
    ('select',    1,  'B'),
    ('enable',    1,  'B'),
    ('command',   1,  'B'),
    ('dataLen',   4, '<i'),
    ('bits',      4, '<i'),
    ('state',     4, None),
    ('data',     12, None),
    ('reserved', 12, None),
    ('reserved2', 1,  '?'),
    ('reserved3', 4, '<I'),
]

# VBA EEPROM save data struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L20-L29
VBA_EEPROM_SAVE_DATA_STRUCT = [
    ('eepromMode',                  4, '<i'),
    ('eepromByte',                  4, '<i'),
    ('eepromBits',                  4, '<i'),
    ('eepromAddress',               4, '<i'),
    ('eepromInUse',                 1,  '?'),
    ('eepromData', SIZE['EEPROM_512'], None),
    ('eepromBuffer',               16, None),
]

# VBA flash save data struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/gba/Flash.cpp#L237-L242
VBA_FLASH_SAVE_DATA_1_STRUCT = [
    ('flashState',                      4, '<i'),
    ('flashReadState',                  4, '<i'),
    ('flashSaveMemory', SIZE['FLASH_512'], None),
]
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/gba/Flash.cpp#L244-L250
VBA_FLASH_SAVE_DATA_2_STRUCT = [
    ('flashState',                      4, '<i'),
    ('flashReadState',                  4, '<i'),
    ('flashSize',                       4, '<i'),
    ('flashSaveMemory',  SIZE['FLASH_1M'], None),
]
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/gba/Flash.cpp#L216-L223
VBA_FLASH_SAVE_DATA_3_STRUCT = [
    ('flashState',                      4, '<i'),
    ('flashReadState',                  4, '<i'),
    ('flashSize',                       4, '<i'),
    ('flashBank',                       4, '<i'),
    ('flashSaveMemory',  SIZE['FLASH_1M'], None),
]

# VBA old GBA state struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L603-L678
VBA_OLD_GBA_STATE_STRUCT = [
    ('soundPaused',             4, '<i'),
    ('soundPlay',               4, '<i'),
    ('soundTicks',              4, '<i'),
    ('SOUND_CLOCK_TICKS',       4, '<i'),
    ('soundLevel1',             4, '<i'),
    ('soundLevel2',             4, '<i'),
    ('soundBalance',            4, '<i'),
    ('soundMasterOn',           4, '<i'),
    ('soundIndex',              4, '<i'),
    ('sound1On',                4, '<i'),
    ('sound1ATL',               4, '<i'),
    ('sound1Skip',              4, '<i'),
    ('sound1Index',             4, '<i'),
    ('sound1Continue',          4, '<i'),
    ('sound1EnvelopeVolume',    4, '<i'),
    ('sound1EnvelopeATL',       4, '<i'),
    ('sound1EnvelopeATLReload', 4, '<i'),
    ('sound1EnvelopeUpDown',    4, '<i'),
    ('sound1SweepATL',          4, '<i'),
    ('sound1SweepATLReload',    4, '<i'),
    ('sound1SweepSteps',        4, '<i'),
    ('sound1SweepUpDown',       4, '<i'),
    ('sound1SweepStep',         4, '<i'),
    ('sound2On',                4, '<i'),
    ('sound2ATL',               4, '<i'),
    ('sound2Skip',              4, '<i'),
    ('sound2Index',             4, '<i'),
    ('sound2Continue',          4, '<i'),
    ('sound2EnvelopeVolume',    4, '<i'),
    ('sound2EnvelopeATL',       4, '<i'),
    ('sound2EnvelopeATLReload', 4, '<i'),
    ('sound2EnvelopeUpDown',    4, '<i'),
    ('sound3On',                4, '<i'),
    ('sound3ATL',               4, '<i'),
    ('sound3Skip',              4, '<i'),
    ('sound3Index',             4, '<i'),
    ('sound3Continue',          4, '<i'),
    ('sound3OutputLevel',       4, '<i'),
    ('sound4On',                4, '<i'),
    ('sound4ATL',               4, '<i'),
    ('sound4Skip',              4, '<i'),
    ('sound4Index',             4, '<i'),
    ('sound4Clock',             4, '<i'),
    ('sound4ShiftRight',        4, '<i'),
    ('sound4ShiftSkip',         4, '<i'),
    ('sound4ShiftIndex',        4, '<i'),
    ('sound4NSteps',            4, '<i'),
    ('sound4CountDown',         4, '<i'),
    ('sound4Continue',          4, '<i'),
    ('sound4EnvelopeVolume',    4, '<i'),
    ('sound4EnvelopeATL',       4, '<i'),
    ('sound4EnvelopeATLReload', 4, '<i'),
    ('sound4EnvelopeUpDown',    4, '<i'),
    ('soundEnableFlag',         4, '<i'),
    ('soundControl',            4, '<i'),
    ('pcm[0].readIndex',        4, '<i'),
    ('pcm[0].count',            4, '<i'),
    ('pcm[0].writeIndex',       4, '<i'),
    ('soundDSAEnabled',         1,  'B'),
    ('soundDSATimer',           4, '<i'),
    ('pcm[0].fifo',            32, None),
    ('state.soundDSAValue',     1,  'B'),
    ('pcm[1].readIndex',        4, '<i'),
    ('pcm[1].count',            4, '<i'),
    ('pcm[1].writeIndex',       4, '<i'),
    ('soundDSBEnabled',         4, '<i'),
    ('soundDSBTimer',           4, '<i'),
    ('pcm[1].fifo',            32, None),
    ('state.soundDSBValue',     4, '<i'),
]

# VBA old GBA state 2 struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L680-L686
VBA_OLD_GBA_STATE2_STRUCT = [
    ('state.apu.regs',    32, None),
    ('sound3Bank',         4, '<i'),
    ('sound3DataSize',     4, '<i'),
    ('sound3ForcedOutput', 4, '<i'),
]

# VBA GBA state struct elements as (NAME, SIZE IN BYTES, STRUCT FORMAT STRING) tuples
# https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L690-L737
VBA_GBA_STATE_STRUCT = [
    ('pcm[0].readIndex',              4, '<i'),
    ('pcm[0].count',                  4, '<i'),
    ('pcm[0].writeIndex',             4, '<i'),
    ('pcm[0].fifo',                  32, None),
    ('pcm[0].dac',                    4, '<i'),
    ('pcm[0].room_for_expansion',    16, None),
    ('pcm[1].readIndex',              4, '<i'),
    ('pcm[1].count',                  4, '<i'),
    ('pcm[1].writeIndex',             4, '<i'),
    ('pcm[1].fifo',                  32, None),
    ('pcm[1].dac',                    4, '<i'),
    ('pcm[1].room_for_expansion',    16, None),
    ('state.apu.regs',               64, None),
    ('state.apu.frame_time',          4, '<i'),
    ('state.apu.frame_phase',         4, '<i'),
    ('state.apu.sweep_freq',          4, '<i'),
    ('state.apu.sweep_delay',         4, '<i'),
    ('state.apu.sweep_enabled',       4, '<i'),
    ('state.apu.sweep_neg',           4, '<i'),
    ('state.apu.noise_divider',       4, '<i'),
    ('state.apu.wave_buf',            4, '<i'),
    ('state.apu.delay',              16, None),
    ('state.apu.length_ctr',         16, None),
    ('state.apu.phase',              16, None),
    ('state.apu.enabled',            16, None),
    ('state.apu.env_delay',          12, None),
    ('state.apu.env_volume',         12, None),
    ('state.apu.env_enabled',        12, None),
    ('state.apu.room_for_expansion', 52, None),
    ('soundEnableFlag',               4, '<i'),
    ('soundTicks',                    4, '<i'),
    ('emulator.room_for_expansion',  56, None),
]

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
        data = gopen(filename).read(); ind = 0
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
            self.irq_tricks = unpack('<i', data[ind:ind+4])[0]; ind += 4
            if self.irq_tricks > 0:
                self.int_state = True
            else:
                self.irq_tricks = 0
                self.int_state = False
        self.iram = data[ind:ind+SIZE['IRAM']]; ind += SIZE['IRAM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L834
        self.pram = data[ind:ind+SIZE['PRAM']]; ind += SIZE['PRAM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L835
        self.wram = data[ind:ind+SIZE['WRAM']]; ind += SIZE['WRAM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L836
        self.vram = data[ind:ind+SIZE['VRAM']]; ind += SIZE['VRAM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L837
        self.oam = data[ind:ind+SIZE['OAM']]; ind += SIZE['OAM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L838
        self.pix = data[ind:ind+SIZE['PIX']]; ind += SIZE['PIX'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L839-L842
        self.iomem = data[ind:ind+SIZE['IOMEM']]; ind += SIZE['IOMEM'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L843
        self.eeprom_save_data = dict()
        for n, s, f in VBA_EEPROM_SAVE_DATA_STRUCT: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L72
            if f is None:
                self.eeprom_save_data[n] = data[ind:ind+s]; ind += s
            else:
                self.eeprom_save_data[n] = unpack(f, data[ind:ind+s])[0]; ind += s
        if self.save_game_version < 3: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L73-L79
            self.eeprom_size = SIZE['EEPROM_512'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L78
        else:
            self.eeprom_size = unpack('<i', data[ind:ind+4])[0]; ind += 4 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L74
            self.eeprom_data = data[ind:ind+SIZE['EEPROM_8K']]; ind += SIZE['EEPROM_8K'] # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/EEprom.cpp#L75
        if self.save_game_version < 5:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_1_STRUCT
        elif self.save_game_version < 7:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_2_STRUCT
        else:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_3_STRUCT
        self.flash_save_data = dict()
        for n, s, f in flash_save_data_struct:
            if f is None:
                self.flash_save_data[n] = data[ind:ind+s]; ind += s
            else:
                self.flash_save_data[n] = unpack(f, data[ind:ind+s])[0]; ind += s
        if self.save_game_version > 9: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L808
            self.gba_state = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L809
            for n, s, f in VBA_GBA_STATE_STRUCT:
                if f is None:
                    self.gba_state[n] = data[ind:ind+s]; ind += s
                else:
                    self.gba_state[n] = unpack(f, data[ind:ind+s])[0]; ind += s
        else: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L811
            self.old_gba_state = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L768
            for n, s, f in VBA_OLD_GBA_STATE_STRUCT: # TODO HERE DOCS
                if f is None:
                    self.old_gba_state[n] = data[ind:ind+s]; ind += s
                else:
                    self.old_gba_state[n] = unpack(f, data[ind:ind+s])[0]; ind += s
            ind += 5880 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L769
            if version >= 3: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L790
                self.old_gba_state2 = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L791
                for n, s, f in VBA_OLD_GBA_STATE2_STRUCT:
                    if f is None:
                        self.old_gba_state2[n] = data[ind:ind+s]; ind += s
                    else:
                        self.old_gba_state2[n] = unpack(f, data[ind:ind+s])[0]; ind += s
            ind += 4 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Sound.cpp#L797
        if self.save_game_version > 1: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L856-L863
            num_cheats = min(VBA_MAX_CHEATS, unpack('<i', data[ind:ind+4])[0]); ind += 4 # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Cheats.cpp#L2591
            self.cheats_list = [None]*num_cheats
            for i in range(num_cheats):
                cheat = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/8f1b5dae904a48a10b1a27ff6f1de72d451454a6/src/gba/Cheats.cpp#L2602-L2613
                cheat['code'] = unpack('<i', data[ind:ind+4])[0]; ind += 4
                cheat['size'] = unpack('<i', data[ind:ind+4])[0]; ind += 4
                cheat['status'] = unpack('<i', data[ind:ind+4])[0]; ind += 4
                if self.save_game_version < 9:
                    cheat['enabled'] = False if unpack('<i', data[ind:ind+4])[0] == 0 else True; ind += 4
                else:
                    cheat['enabled'] = unpack('?', data[ind:ind+1])[0]; ind += 1
                if self.save_game_version >= 9:
                    cheat['rawaddress'] = unpack('<I', data[ind:ind+4])[0]; ind += 4
                cheat['address'] = unpack('<I', data[ind:ind+4])[0]; ind += 4
                if self.save_game_version < 9:
                    cheat['rawaddress'] = cheat['address']
                cheat['value'] = unpack('<I', data[ind:ind+4])[0]; ind += 4
                cheat['oldValue'] = unpack('<I', data[ind:ind+4])[0]; ind += 4
                cheat['codestring'] = common.bytes_to_str(data[ind:ind+20]); ind += 20
                cheat['desc'] = common.bytes_to_str(data[ind:ind+32]); ind += 32
                self.cheats_list[i] = cheat
            if self.save_game_version >= 9:
                ind += ((VBA_MAX_CHEATS - num_cheats) * 81)
        if self.save_game_version > 6: # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/f1d3f631d214b8337e1b98fde2b01c867ede1214/src/gba/GBA.cpp#L864-L866
            self.rtc_clock_data = dict() # https://github.com/visualboyadvance-m/visualboyadvance-m/blob/ae09ae7d591fb3ff78abbe3f762184534905405d/src/gba/RTC.cpp#L19-L33
            for n, s, f in VBA_RTC_CLOCK_DATA_STRUCT:
                if f is None:
                    self.rtc_clock_data[n] = data[ind:ind+s]; ind += s
                else:
                    self.rtc_clock_data[n] = unpack(f, data[ind:ind+s])[0]; ind += s
        print(len(data)); print(ind); exit() # TODO DELETE WHEN DONE

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
        out.write(self.iram)
        out.write(self.pram)
        out.write(self.wram)
        out.write(self.vram)
        out.write(self.oam)
        out.write(self.pix)
        out.write(self.iomem)
        for n, s, f in VBA_EEPROM_SAVE_DATA_STRUCT:
            if f is None:
                out.write(self.eeprom_save_data[n])
            else:
                out.write(pack(f, self.eeprom_save_data[n]))
        if self.save_game_version >= 3:
            out.write(pack('<i', self.eeprom_size))
            out.write(self.eeprom_data)
        if self.save_game_version < 5:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_1_STRUCT
        elif self.save_game_version < 7:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_2_STRUCT
        else:
            flash_save_data_struct = VBA_FLASH_SAVE_DATA_3_STRUCT
        for n, s, f in flash_save_data_struct:
            if f is None:
                out.write(self.flash_save_data[n])
            else:
                out.write(pack(f, self.flash_save_data[n]))
        # TODO GBA STATE STUFF
        for i in range(len(self.cheats_list)):
            cheat = cheats_list[i]
            out.write(pack('<i', cheat['code']))
            out.write(pack('<i', cheat['size']))
            out.write(pack('<i', cheat['status']))
            if self.save_game_version < 9:
                out.write(pack('<i', {True:1,False:0}[cheat['enabled']]))
            else:
                out.write(pack('?', cheat['enabled']))
            if self.game_version >= 9:
                out.write(pack('<I', cheat['rawaddress']))
            out.write(pack('<I', cheat['address']))
            out.write(pack('<I', cheat['value']))
            out.write(pack('<I', cheat['oldValue']))
            out.write(bytes([ord(c) for c in cheat['codestring']] + [0]*(20-len(cheat['codestring']))))
            out.write(bytes([ord(c) for c in cheat['desc']] + [0]*(32-len(cheat['desc']))))
        if self.save_game_version >= 9:
            out.write(bytes([0]*(81*(VBA_MAX_CHEATS-len(self.cheats_list)))))
        for n, s, f in VBA_RTC_CLOCK_DATA_STRUCT:
            if f is None:
                out.write(self.rtc_clock_data[n])
            else:
                out.write(pack(f, self.rtc_clock_data[n]))
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
        f.write("- IRAM Size: %d bytes%s" % (len(self.iram), end))
        f.write("- PRAM Size: %d bytes%s" % (len(self.pram), end))
        f.write("- WRAM Size: %d bytes%s" % (len(self.wram), end))
        f.write("- VRAM Size: %d bytes%s" % (len(self.vram), end))
        f.write("- OAM Size: %d bytes%s" % (len(self.oam), end))
        f.write("- PIX Size: %d bytes%s" % (len(self.pix), end))
        f.write("- IOMEM Size: %d bytes%s" % (len(self.iomem), end))
        f.write("- EEPROM Save Data: %d items%s" % (len(self.eeprom_save_data), end))
        for n, _, __ in VBA_EEPROM_SAVE_DATA_STRUCT:
            if __ is None:
                f.write("  - %s Size: %d bytes%s" % (n, len(self.eeprom_save_data[n]), end))
            else:
                f.write("  - %s: %s%s" % (n, self.eeprom_save_data[n], end))
        f.write("- EEPROM Size: %d%s" % (self.eeprom_size, end))
        if self.save_game_version >= 3:
            f.write("- EEPROM Data Size: %d bytes%s" % (len(self.eeprom_data), end))
        f.write("- Flash Save Data: %d items%s" % (len(self.flash_save_data), end))
        for k, v in self.flash_save_data.items():
            if isinstance(v, bytes):
                f.write("  - %s Size: %d bytes%s" % (k, len(v), end))
            else:
                f.write("  - %s: %s%s" % (k, v, end))
        # TODO GBA STATE STUFF
        f.write("- Cheats List: %d cheats%s" % (len(self.cheats_list), end))
        for cheat_ind, cheat in enumerate(self.cheats_list):
            f.write("  - Cheat %d:%s" % (cheat_ind+1, end))
            f.write("    - Name: %s%s" % (cheat['codestring'], end))
            f.write("    - Description: %s%s" % (cheat['desc'], end))
            f.write("    - Enabled: %s%s" % (cheat['enabled'], end))
            f.write("    - Raw Address: %s%s" % (common.byte_to_hex_str(cheat['rawaddress'], length=8), end))
            f.write("    - Address: %s%s" % (common.byte_to_hex_str(cheat['address'], length=8), end))
            f.write("    - Value: %d%s" % (cheat['value'], end))
            f.write("    - Old Value: %d%s" % (cheat['oldValue'], end))
        f.write("- RTC Clock Data: %d items%s" % (len(self.rtc_clock_data), end))
        for n, _, __ in VBA_RTC_CLOCK_DATA_STRUCT:
            if __ is None:
                f.write("  - %s Size: %d bytes%s" % (n, len(self.rtc_clock_data[n]), end))
            else:
                f.write("  - %s: %s%s" % (n, self.rtc_clock_data[n], end))
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

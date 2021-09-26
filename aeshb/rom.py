#!/usr/bin/env python3

from math import log2
from collections.abc import Sequence
import random

from toolz import partition

from nmigen import *
from nmigen.cli import main

from aeshb.le import LELUT4
from aeshb.utils import bitlist2int
from aeshb.simpleaes import SimpleAES


def cascade_depthwise(m, addr_l, data_l, addr_h, data_h):
    assert len(addr_l) == len(addr_h) and len(data_l) == len(data_h)
    addr = Signal(len(addr_l) + 1)
    data = Signal.like(data_l)
    m.d.comb += [
        addr_l.eq(addr[:-1]),
        addr_h.eq(addr[:-1]),
    ]
    with m.If(addr[-1]):
        m.d.comb += data.eq(data_h)
    with m.Else():
        m.d.comb += data.eq(data_l)
    return addr, data

class ROM16x1(Elaboratable):
    depth = 16
    width = 1

    def __init__(self, addr, init):
        self.addr = addr
        if isinstance(init, int):
            assert 0 <= init < 2**16
        else:
            assert isinstance(init, Sequence) and len(init) == 16
            init = bitlist2int(init)
        self.init = init
        self.data = Signal()
        self.lut4 = LELUT4(self.addr, mask=self.init)
        self.lut4.combout.name = "data"

    def elaborate(self, platform):
        m = Module()
        m.submodules.rom16x1_lut4 = self.lut4
        m.d.comb += self.data.eq(self.lut4.combout)
        return m

    def ports(self):
        return [self.addr, self.data]


class ROM16x8(Elaboratable):
    depth = 16
    width = 8

    def __init__(self, addr, init):
        self.addr = addr
        self.data = Signal(self.width)
        if isinstance(init, Sequence):
            assert all(0 <= n <= 2 ** self.width for n in init)
            init = bytes(init)
        assert isinstance(init, bytes) and len(init) == self.depth
        self.init = init
        self.masks = [0] * self.width
        for i in range(self.width):
            for j in range(self.depth):
                self.masks[i] |= ((self.init[j] >> i) & 1) << j
        self.lut4 = []
        for i in range(self.width):
            lut4 = LELUT4(self.addr, mask=self.masks[i])
            lut4.combout.name = f"data{i}"
            self.lut4.append(lut4)

    def elaborate(self, platform):
        m = Module()
        for i, lut4 in enumerate(self.lut4):
            m.submodules[f"lut4_b{i}"] = lut4
            m.d.comb += self.data[i].eq(lut4.combout)
        return m

    def ports(self):
        return [self.addr, self.data]


class ROM16x16(Elaboratable):
    depth = 16
    width = 16

    def __init__(self, addr, init):
        self.addr = addr
        self.data = Signal(self.width)
        assert isinstance(init, Sequence) and len(init) == self.depth
        assert all(0 <= n <= 2 ** self.width for n in init)
        self.init = init
        self.masks = [0] * self.width
        for i in range(self.width):
            for j in range(self.depth):
                self.masks[i] |= ((self.init[j] >> i) & 1) << j
        self.lut4 = []
        for i in range(self.width):
            lut4 = LELUT4(self.addr, mask=self.masks[i])
            lut4.combout.name = f"data{i}"
            self.lut4.append(lut4)

    def elaborate(self, platform):
        m = Module()
        for i, lut4 in enumerate(self.lut4):
            m.submodules[f"lut4_b{i}"] = lut4
            m.d.comb += self.data[i].eq(lut4.combout)
        return m

    def ports(self):
        return [self.addr, self.data]


class ROM32x16(Elaboratable):
    depth = 32
    width = 16

    def __init__(self, addr, init, pipelined=False):
        self.addr = addr
        self.data = Signal(self.width)
        self.pipelined = pipelined
        assert isinstance(init, Sequence) and len(init) == self.depth
        assert all(0 <= n <= 2 ** self.width for n in init)
        self.init = init
        self.rom_addr = Signal(int(log2(ROM16x16.width)))
        self.rom_inits = list(partition(ROM16x16.depth, init))
        self.roms = []
        for i in range(self.depth // ROM16x16.depth):
            rom = ROM16x16(self.rom_addr, init=self.rom_inits[i])
            self.roms.append(rom)

    def elaborate(self, platform):
        m = Module()
        for i, rom in enumerate(self.roms):
            m.submodules[f"rom32x16_subrom16x16_{i}"] = rom
        m.d.comb += self.rom_addr.eq(self.addr[:len(self.rom_addr)])

        self.addr_data_32 = []
        for rom_l, rom_h in partition(2, self.roms):
            addr_32, data_32 = cascade_depthwise(m, rom_l.addr, rom_l.data, rom_h.addr, rom_h.data)
            if self.pipelined:
                data_32_reg = Signal.like(data_32)
                m.d.sync += data_32_reg.eq(data_32)
                data_32 = data_32_reg
            self.addr_data_32.append((addr_32, data_32))

        m.d.comb += self.addr_data_32[0][0].eq(self.addr)
        m.d.comb += self.data.eq(self.addr_data_32[0][1])

        return m

    def ports(self):
        return [self.addr, self.data]


class ROM128x16(Elaboratable):
    depth = 128
    width = 16

    def __init__(self, addr, init, pipelined=False):
        self.addr = addr
        self.data = Signal(self.width)
        self.pipelined = pipelined
        assert isinstance(init, Sequence) and len(init) == self.depth
        assert all(0 <= n <= 2 ** self.width for n in init)
        self.init = init
        self.rom_addr = Signal(int(log2(ROM16x16.width)))
        self.rom_inits = list(partition(ROM16x16.depth, init))
        self.roms = []
        for i in range(self.depth // ROM16x16.depth):
            rom = ROM16x16(self.rom_addr, init=self.rom_inits[i])
            self.roms.append(rom)

    def elaborate(self, platform):
        m = Module()
        for i, rom in enumerate(self.roms):
            m.submodules[f"rom128x16_subrom16x16_{i}"] = rom
        m.d.comb += self.rom_addr.eq(self.addr[:len(self.rom_addr)])

        self.addr_data_32 = []
        for rom_l, rom_h in partition(2, self.roms):
            addr_32, data_32 = cascade_depthwise(m, rom_l.addr, rom_l.data, rom_h.addr, rom_h.data)
            self.addr_data_32.append((addr_32, data_32))

        self.addr_data_64 = []
        for rom_l, rom_h in partition(2, self.addr_data_32):
            addr_64, data_64 = cascade_depthwise(m, rom_l[0], rom_l[1], rom_h[0], rom_h[1])
            self.addr_data_64.append((addr_64, data_64))

        self.addr_data_128 = []
        for rom_l, rom_h in partition(2, self.addr_data_64):
            addr_128, data_128 = cascade_depthwise(m, rom_l[0], rom_l[1], rom_h[0], rom_h[1])
            self.addr_data_128.append((addr_128, data_128))

        m.d.comb += self.addr_data_128[0][0].eq(self.addr)
        m.d.comb += self.data.eq(self.addr_data_128[0][1])

        return m

    def ports(self):
        return [self.addr, self.data]


class ROM256x8(Elaboratable):
    depth = 256
    width = 8

    def __init__(self, addr, init, pipelined=False):
        self.addr = addr
        self.data = Signal(self.width)
        self.pipelined = pipelined
        assert isinstance(init, Sequence) and len(init) == self.depth
        assert all(0 <= n <= 2 ** self.width for n in init)
        self.init = init
        self.rom_addr = Signal(self.width-1)
        self.rom_init = [(x[1] << 8) | x[0] for x in partition(2, init)]
        self.rom = ROM128x16(self.rom_addr, init=self.rom_init, pipelined=pipelined)

    def elaborate(self, platform):
        m = Module()
        m.submodules.rom128x16 = self.rom
        m.d.comb += self.rom_addr.eq(self.addr[1:])
        with m.If(self.addr[0]):
            m.d.comb += self.data.eq(self.rom.data[self.width:])
        with m.Else():
            m.d.comb += self.data.eq(self.rom.data[:self.width])
        return m

    def ports(self):
        return [self.addr, self.data]


if __name__ == "__main__":
    # addr = Signal(4)
    # rom = ROM16x1(addr, init=0xDEAD)
    # static_random = bytes.fromhex("b2c8c5875fa45462afe35753b9b70f43")
    # rom = ROM16x8(addr, init=static_random)
    # static_random = [34502, 10917, 31302, 39655, 62319, 3030, 62137, 43078,
    #                  56956, 59113, 7346, 65069, 22379, 6733, 4648, 4599]
    # rom = ROM16x16(addr, init=static_random)
    addr = Signal(8)
    rom = ROM256x8(addr, init=SimpleAES.sbox)
    # addr = Signal(5)
    # rom = ROM32x16(addr, init=list(range(32)))
    main(rom, ports=[addr, rom.data])

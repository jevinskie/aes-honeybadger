#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

from aeshb.le import LELUT4
from aeshb.utils import bitlist2int

class ROM16x1(Elaboratable):
    def __init__(self, addr, init):
        self.addr = addr
        if isinstance(init, int):
            assert 0 <= init < 2**16
        else:
            assert isinstance(init, list) and len(init) == 16
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
        if isinstance(init, list):
            assert all(0 <= n <= 2 ** self.width for n in init)
            init = bytes(init)
        assert isinstance(init, bytes) and len(init) == self.depth
        self.init = init
        self.masks = [0] * self.width
        for i in range(self.width):
            for j in range(self.depth):
                self.masks[i] |= ((self.init[j] >> i) & 1) << j
        self.data = Signal(self.width)
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
        assert isinstance(init, list) and len(init) == self.depth
        assert all(0 <= n <= 2 ** self.width for n in init)
        self.init = init
        self.masks = [0] * self.width
        for i in range(self.width):
            for j in range(self.depth):
                self.masks[i] |= ((self.init[j] >> i) & 1) << j
        self.data = Signal(self.width)
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

if __name__ == "__main__":
    addr = Signal(4)
    # rom = ROM16x1(addr, init=0xDEAD)
    # static_random = bytes.fromhex("b2c8c5875fa45462afe35753b9b70f43")
    # rom = ROM16x8(addr, init=static_random)
    static_random = [34502, 10917, 31302, 39655, 62319, 3030, 62137, 43078,
                     56956, 59113, 7346, 65069, 22379, 6733, 4648, 4599]
    rom = ROM16x16(addr, init=static_random)
    main(rom, ports=[addr, rom.data])

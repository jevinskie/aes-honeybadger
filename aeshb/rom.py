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

if __name__ == "__main__":
    addr = Signal(4)
    rom = ROM16x1(addr, init=0xDEAD)
    main(rom, ports=[addr, rom.data])

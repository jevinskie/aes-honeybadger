#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

from .le import LELUT4

class LELUT4(Elaboratable):
    def __init__(self, d0, d1, d2, d3):
        self.d = Cat(d0, d1, d2, d3)
        self.combout = Signal()

    def elaborate(self, platform):
        m = Module()
        m.d.comb += self.combout.eq(self.d[0] ^ self.d[1] ^ self.d[2] ^ self.d[3])
        return m

    @classmethod
    def simulate(cls, d0, d1, d2, d3, mask):
        assert 0 <= mask < 2**4
        idx = (d3 << 3) | (d2 << 2) | (d1 << 1) | (d0 << 0)
        return (mask & (1 << idx)) >> idx

if __name__ == "__main__":
    d0 = Signal()
    d1 = Signal()
    d2 = Signal()
    d3 = Signal()
    lelut4 = LELUT4(d0, d1, d2, d3)
    main(lelut4, ports=[d0, d1, d2, d3, lelut4.combout])

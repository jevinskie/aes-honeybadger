#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

class LELUT4(Elaboratable):
    def __init__(self, d0, d1, d2, d3):
        self.d = Cat(d0, d1, d2, d3)
        self.combout = Signal()

    def elaborate(self, platform):
        m = Module()
        m.d.comb += self.combout.eq(self.d[0] ^ self.d[1] ^ self.d[2] ^ self.d[3])
        return m

if __name__ == "__main__":
    d0 = Signal()
    d1 = Signal()
    d2 = Signal()
    d3 = Signal()
    lelut4 = LELUT4(d0, d1, d2, d3)
    main(lelut4, ports=[d0, d1, d2, d3, lelut4.combout])

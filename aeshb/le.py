#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main
from nmigen.lib.fpga_lut import LUTInput, LUTOutput

class LELUT(Elaboratable):
    def __init__(self, d, mask: int):
        self.d = d
        assert 0 <= mask < 2**16
        self.mask = mask
        self.combout = Signal()

    def elaborate(self, platform):
        m = Module()
        self.d_li = []
        for i in range(4):
            lis = Signal(name=f"lut4_li{i}")
            li = LUTInput(self.d[i], lis)
            self.d_li.append(lis)
            m.submodules[f"lut4_li{i}"] = li
        self.d_li = Cat(*self.d_li)
        self.combout_lo_sig = Signal(name="lut4_lo")
        m.d.comb += self.combout_lo_sig.eq(Const(self.mask, 16).bit_select(self.d_li, 1))
        lo = LUTOutput(self.combout_lo_sig, self.combout)
        m.submodules += lo
        return m

    @classmethod
    def simulate(cls, d0, d1, d2, d3, mask):
        assert 0 <= mask < 2**16
        idx = (d3 << 3) | (d2 << 2) | (d1 << 1) | (d0 << 0)
        return (mask & (1 << idx)) >> idx

class LELUT4Atom(Elaboratable):
    def __init__(self, d, mask: int):
        self.d = d
        assert 0 <= mask < 2**16
        self.mask = mask
        self.combout = Signal()

    def elaborate(self, platform):
        m = Module()
        self.d_li = []
        for i in range(4):
            lis = Signal(name=f"lut4_li{i}")
            li = LUTInput(self.d[i], lis)
            self.d_li.append(lis)
            m.submodules += li
        self.d_li = Cat(*self.d_li)
        self.combout_lo_sig = Signal(name="lut4_lo")
        m.d.comb += self.combout_lo_sig.eq(Const(self.mask, 16).bit_select(self.d_li, 1))
        lo = LUTOutput(self.combout_lo_sig, self.combout)
        m.submodules += lo
        return m


if __name__ == "__main__":
    d = Signal(4)
    lelut4 = LELUT4(d, mask=0xFF00)
    main(lelut4, ports=[d, lelut4.combout])

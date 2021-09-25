#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main
from nmigen.lib.fpga_lut import LUTInput, LUTOutput

from aeshb.utils import int2bitlist

class LELUT4(Elaboratable):
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
            m.submodules[f"lut4_li{i}_mod"] = li
        self.d_li = Cat(*self.d_li)
        self.lut_mask_sig = Signal(16, name="lut_mask")
        m.d.comb += self.lut_mask_sig.eq(Const(self.mask, 16))
        self.combout_lo_sig = Signal(name="lut4_lo")
        m.d.comb += self.combout_lo_sig.eq(self.lut_mask_sig.bit_select(self.d_li, 1))
        lo = LUTOutput(self.combout_lo_sig, self.combout)
        m.submodules["lut4_lo_mod"] = lo
        return m

    @classmethod
    def simulate(cls, d0, d1, d2, d3, mask):
        assert 0 <= mask < 2**16
        idx = (d3 << 3) | (d2 << 2) | (d1 << 1) | (d0 << 0)
        return (mask >> idx) & 1

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
    lelut4 = LELUT4(d, mask=0xDEAD)
    mask_orig = 0xDEAD
    mask_new = 0xBCEB
    mask_new2 = 0xF6B9
    for i in range(16):
        d3o, d2o, d1o, d0o = reversed(int2bitlist(i, 4))
        d3n, d2n, d1n, d0n = d2o, d3o, d0o, d1o
        d3n2, d2n2, d1n2, d0n2 = d0o, d1o, d2o, d3o
        o = LELUT4.simulate(d0o, d1o, d2o, d3o, mask=mask_orig)
        n = LELUT4.simulate(d0n, d1n, d2n, d3n, mask=mask_new)
        n2 = LELUT4.simulate(d0n2, d1n2, d2n2, d3n2, mask=mask_new2)
        print(f"i: {i:2} orig: {o} new: {n} new2: {n2}")
    # main(lelut4, ports=[d, lelut4.combout])

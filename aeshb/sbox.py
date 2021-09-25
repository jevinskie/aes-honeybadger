#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

from aeshb.simpleaes import SimpleAES

class SBoxROMLUT(Elaboratable):
    def __init__(self, in_byte: Signal):
        assert len(in_byte) == 8
        self.in_byte = in_byte
        self.out_byte = Signal(8)
        self.mem = Memory(width=8, depth=len(SimpleAES.sbox), init=SimpleAES.sbox)

    def elaborate(self, platform):
        m = Module()

        m.submodules.rd_port = rd_port = self.mem.read_port()
        m.d.comb += [
            rd_port.addr.eq(self.in_byte),
            self.out_byte.eq(rd_port.data),
        ]
        return m

class SBoxROMLUTSplit2x(Elaboratable):
    def __init__(self, in_byte: Signal):
        assert len(in_byte) == 8
        self.in_byte = in_byte
        self.out_byte = Signal(8)
        self.mem_l = Memory(width=8, depth=128, init=SimpleAES.sbox[:128])
        self.mem_h = Memory(width=8, depth=128, init=SimpleAES.sbox[128:])

    def elaborate(self, platform):
        m = Module()

        m.submodules.rd_l_port = rd_l_port = self.mem_l.read_port()
        m.submodules.rd_h_port = rd_h_port = self.mem_h.read_port()
        bank_sel_reg = Signal(reset_less=True)
        rd_l_reg = Signal(8, reset_less=True)
        rd_h_reg = Signal(8, reset_less=True)
        m.d.sync += [
            bank_sel_reg.eq(self.in_byte[-1]),
            rd_l_reg.eq(rd_l_port.data),
            rd_h_reg.eq(rd_h_port.data),
        ]
        m.d.comb += [
            rd_l_port.addr.eq(self.in_byte[:-1]),
            rd_h_port.addr.eq(self.in_byte[:-1]),
        ]
        with m.If(bank_sel_reg):
            m.d.comb += self.out_byte.eq(rd_h_reg)
        with m.Else():
            m.d.comb += self.out_byte.eq(rd_l_reg)
        return m

if __name__ == "__main__":
    in_byte = Signal(8)
    sbox = SBoxROMLUTSplit2x(in_byte)
    main(sbox, ports=[sbox.in_byte, sbox.out_byte])

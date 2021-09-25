#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

from aeshb.simpleaes import SimpleAES

class SBoxROMLUT(Elaboratable):
    def __init__(self, in_byte: Signal):
        assert len(in_byte) == 8
        self.in_byte = in_byte
        self.out_byte_reg = Signal(8, reset_less=True)
        self.out_byte = Signal(8)
        def next_pow2(x):
            return 1 << (x - 1).bit_length()
        sz = next_pow2(len(SimpleAES.sbox))
        self.mem = Memory(width=8, depth=sz, init=SimpleAES.sbox)

    def elaborate(self, platform):
        m = Module()

        m.submodules.rd_port = rd_port = self.mem.read_port()
        self.addr = Signal.like(rd_port.addr)
        m.d.comb += [
            self.addr.eq(self.in_byte),
            rd_port.addr.eq(self.addr),
            self.out_byte.eq(self.out_byte_reg),
        ]
        m.d.sync += self.out_byte_reg.eq(rd_port.data)
        return m

if __name__ == "__main__":
    in_byte = Signal(8)
    sbox = SBoxROMLUT(in_byte)
    main(sbox, ports=[sbox.in_byte, sbox.out_byte])

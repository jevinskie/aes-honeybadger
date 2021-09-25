#!/usr/bin/env python3

from nmigen import *
from nmigen_boards.arrow_deca import *
from nmigen.hdl.rec import *
from nmigen.lib.io import *
from nmigen.build.dsl import *
from nmigen.build.res import *

from aeshb.sbox import SBoxROMLUT

class Harness(Elaboratable):
    def __init__(self, in_byte, out_byte):
        self.in_byte = in_byte
        self.out_byte = out_byte

    def elaborate(self, platform):
        m = Module()
        self.in_byte_reg = Signal.like(self.in_byte)
        m.d.sync += self.in_byte_reg.eq(self.in_byte)
        m.submodules.sbox = sbox = SBoxROMLUT(self.in_byte_reg)
        m.d.comb += [
            self.out_byte.eq(sbox.out_byte)
        ]
        return m


if __name__ == "__main__":
    platform = ArrowDECAPlatform()
    platform.add_resources([
        Resource("sbox", 0,
            Subsignal("in_byte", Pins("1 2 3 4 5 6 7 8", dir="i",conn=("gpio", 0), assert_width=8)),
            Subsignal("out_byte", Pins("9 10 11 12 13 14 15 16", dir="o", conn=("gpio", 0), assert_width=8)),
            Attrs(io_standard="3.3-V LVTTL"),
        )])
    gpio = platform.request("sbox", 0)
    # platform.add_connectors(platform.connectors.)
    platform.build(Harness(gpio.in_byte, gpio.out_byte), do_program=False)

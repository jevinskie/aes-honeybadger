#!/usr/bin/env python3
import argparse

from nmigen import *
from nmigen_boards.arrow_deca import *
from nmigen.hdl.rec import *
from nmigen.lib.io import *
from nmigen.build.dsl import *
from nmigen.build.res import *

from aeshb.rom import ROM16x1, ROM16x8, ROM16x16, ROM32x16, ROM128x16, ROM256x8
from harnessio import HarnessIO
from aeshb.simpleaes import SimpleAES

class DECA(ArrowDECAPlatform):
    @property
    def file_templates(self):
        # Configure the voltages of the I/O banks by appending the global
        # assignments to the template. However, we create our own copy of the
        # file templates before modifying them to avoid modifying the original.
        return {
            **super().file_templates,
            "{{name}}.qsf":
                super().file_templates.get("{{name}}.qsf") +
                r"""
                """,
        }


class Harness(Elaboratable):
    def __init__(self, sclk, copi, cipo, load):
        self.sclk = sclk
        self.copi = copi
        self.cipo = cipo
        self.load = load

    def elaborate(self, platform):
        m = Module()

        addr = Signal(8)
        # m.submodules.rom = rom = ROM16x1(addr, init=0xDEAD)
        # static_random = bytes.fromhex("b2c8c5875fa45462afe35753b9b70f43")
        # m.submodules.rom = rom = ROM16x8(addr, init=static_random)
        # static_random = [34502, 10917, 31302, 39655, 62319, 3030, 62137, 43078,
        #                  56956, 59113, 7346, 65069, 22379, 6733, 4648, 4599]
        # m.submodules.rom = rom = ROM16x16(addr, init=static_random)
        m.submodules.rom = rom = ROM256x8(addr, init=SimpleAES.sbox)
        inputs = [addr]
        outputs = [rom.data]

        m.submodules.hio = hio = HarnessIO(self.sclk, self.copi, self.cipo, self.load, inputs=inputs, outputs=outputs)
        return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--prog", action="store_true")
    args = parser.parse_args()
    platform = DECA()
    platform.add_resources([
        Resource("harness_spi", 0,
            Subsignal("sclk", Pins("1", dir="i",conn=("gpio", 0))),
            Subsignal("copi", Pins("2", dir="i", conn=("gpio", 0))),
            Subsignal("cipo", Pins("3", dir="o", conn=("gpio", 0))),
            Subsignal("load", Pins("4", dir="i", conn=("gpio", 0))),
            Attrs(io_standard="3.3-V LVTTL"),
        )])
    hio_spi = platform.request("harness_spi", 0)
    harness = Harness(hio_spi.sclk, hio_spi.copi, hio_spi.cipo, hio_spi.load)
    platform.build(harness, name="sbox_bench", do_build=args.build, do_program=args.prog)

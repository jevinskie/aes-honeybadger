#!/usr/bin/env python3
import argparse

from nmigen import *
from nmigen_boards.arrow_deca import *
from nmigen.hdl.rec import *
from nmigen.lib.io import *
from nmigen.build.dsl import *
from nmigen.build.res import *

from aeshb.rom import ROM16x1
from harnessio import HarnessIO

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

        addr = Signal(4)
        m.submodules.rom = rom = ROM16x1(addr, init=0xDEAD)
        inputs = [addr]
        outputs = [rom.data]

        m.submodules.hio = hio = HarnessIO(self.sclk, self.copi, self.cipo, self.load, inputs=inputs, outputs=outputs)
        return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
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
    platform.build(harness, name="sbox_bench", do_build=args.build, do_program=False)

#!/usr/bin/env python3
import argparse

from nmigen import *
from nmigen_boards.arrow_deca import *
from nmigen.hdl.rec import *
from nmigen.lib.io import *
from nmigen.build.dsl import *
from nmigen.build.res import *

from aeshb.jtag import AlteraJTAG, JTAGTAPFSM, JTAGHello

class DECA(ArrowDECAPlatform):
    @property
    def file_templates(self):
        return {
            **super().file_templates,
            "{{name}}.qsf":
                super().file_templates.get("{{name}}.qsf") +
                r"""
                """,
        }

class Blinky(Elaboratable):
    def elaborate(self, platform):
        led   = Cat([platform.request("led", i).o for i in range(8)])
        timer = Signal(32)

        m = Module()
        m.d.sync += timer.eq(timer + 1)
        m.d.comb += led.eq(timer[-8:])
        return m


class JTAGTop(Elaboratable):
    def __init__(self):
        self.jtag_phy = AlteraJTAG()
        self.jtag_hello = JTAGHello(self.jtag_phy)
        self.blinky = Blinky()
        self.ports = None
        self._ports = None

    def elaborate(self, platform):
        m = Module()

        self.a = a = Signal()
        self.b = b = Signal()
        self.c = c = Signal()
        m.d.comb += c.eq(a ^ b)

        m.submodules.jtag_phy = self.jtag_phy
        m.submodules.jtag_hello = self.jtag_hello
        m.submodules.blinky = self.blinky

        return m

    def ports(self):
        raise NotImplementedError()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args()
    platform = DECA()
    jtag_top = JTAGTop()
    platform.build(jtag_top, build_dir="build/jtag_deca", name="jtag_deca", do_build=args.build, do_gen=True, do_program=args.load)

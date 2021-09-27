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


class JTAGTop(Elaboratable):
    def __init__(self):
        self.jtag_phy = AlteraJTAG()
        self.jtag_hello = JTAGHello(self.jtag_phy)

    def elaborate(self, platform):
        m = Module()

        m.submodules.jtag_phy = self.jtag_phy
        m.submodules.jtag_hello = self.jtag_hello

        return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--prog", action="store_true")
    args = parser.parse_args()
    platform = DECA()
    jtag_top = JTAGTop()
    platform.build(jtag_top, build_dir="build/jtag_deca", name="jtag_deca", do_build=args.build, do_program=args.prog)

#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2019 msloniewski <marcin.sloniewski@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import argparse

from migen import *
from migen.genlib.cdc import ClockBuffer
from migen.fhdl.tools import list_clock_domains, list_clock_domains_expr

from litex_boards.platforms import altera_max10_dev_kit

from litex.soc.cores.clock import Max10PLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores import cpu

from liteeth.phy import LiteEthPHY
from liteeth.phy.common import LiteEthPHYMDIO
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.phy.altera_rgmii import LiteEthPHYRGMII

from litescope import LiteScopeAnalyzer

from aeshb.sbox import SBoxROMLUT

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()

        # # #

        # Clk / Rst.
        clk50 = platform.request("clk50")

        # PLL
        self.submodules.pll = pll = Max10PLL(speedgrade="-6")
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(clk50, 50e6)

        pll.create_clkout(self.cd_sys, sys_clk_freq)

# BaseSoC ------------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, platform, clk_freq, sys_clk_freq=int(100e6), **kwargs):
        super().__init__(platform, clk_freq, **kwargs)
        self.platform = platform = altera_max10_dev_kit.Platform()

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, sys_clk_freq,
            ident         = "LiteX SoC on Altera's Max 10 dev kit",
            ident_version = True,
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = self.crg = _CRG(platform, sys_clk_freq)

class FakeSoC(Module):
    def __init__(self):
        self.logger = logging.getLogger("SoC")
        self.cpu_type = None
        class dummy_cr_region:
            origin = 0
            length = 0
            size = 0
            type = "mem"
        self.mem_regions = {'csr': dummy_cr_region()}
        self.constants = {}
        self.csr_regions = {}
        self.csr_map = {}
        self.wb_slaves = {}
        class dummy_bus:
            standard = 'wishbone'
            masters = []
            slaves = []
            data_width = 32
            address_width = 16
            regions = {}
        self.bus = dummy_bus()
        self.mem_map = {}
        self.cpu = cpu.CPUNone()
        class dummy_csr:
            regions = {}
        self.csr = dummy_csr()
        self.irq = None
        self.config = {}

class Harness(SoCCore):
    def __init__(self,
                 sys_clk_freq=int(125e6),
                 **kwargs):
        self.platform = platform = altera_max10_dev_kit.Platform()
        # self.csr_map = {}

        # SoCMini.__init__(self, platform, sys_clk_freq,
        #     ident         = "",
        #     ident_version = False,
        #     **kwargs)
        FakeSoC.__init__(self)


        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        self.sbox_in = Cat([self.platform.request("hsmc_tx_d_p") for i in range(8)])
        self.sbox_in_reg = Signal(8)
        self.sync += self.sbox_in_reg.eq(self.sbox_in)
        self.submodules.sbox = SBoxROMLUT(self.sbox_in)
        self.sbox_out = Signal(8)
        self.sync += self.sbox_out.eq(self.sbox_out)

# Build --------------------------------------------------------------------------------------------

def argparse_set_def(parser: argparse.ArgumentParser, dst: str, default):
    changed = False
    for a in parser._actions:
        if dst == a.dest:
            a.default = default
            return
    raise ValueError(f'dest var {dst} arg not found')

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on DECA")
    parser.add_argument("--build",               action="store_true", help="Build bitstream")
    parser.add_argument("--load",                action="store_true", help="Load bitstream")
    parser.add_argument("--sys-clk-freq",        default=125e6,       help="System clock frequency")
    builder_args(parser)
    soc_core_args(parser)
    argparse_set_def(parser, 'csr_csv', 'csr.csv')
    argparse_set_def(parser, 'uart_baudrate', 3_000_000)
    # argparse_set_def(parser, 'uart_fifo_depth', 1024)
    argparse_set_def(parser, 'cpu_type', 'None')
    argparse_set_def(parser, 'no_uart', True)
    # argparse_set_def(parser, 'cpu_variant', 'minimal')
    argparse_set_def(parser, 'integrated_rom_size', 0*32*1024)
    argparse_set_def(parser, 'integrated_sram_size', 0*4*1024)

    args = parser.parse_args()

    soc = Harness(
        sys_clk_freq             = int(float(args.sys_clk_freq)),
        **soc_core_argdict(args)
    )
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

    # soc.finalize()

    # vns = soc.platform.get_verilog(soc)
    # soc.do_exit(vns=vns)
    # print(vns)

if __name__ == "__main__":
    main()

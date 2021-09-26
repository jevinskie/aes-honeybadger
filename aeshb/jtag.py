#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main
from nmigen.build.dsl import *

import tracemalloc
tracemalloc.start()

class JTAGTAPFSM(Elaboratable):
    def __init__(self, tms):
        self.tms = tms

        # Debug counter
        self.tck_cnt = Signal(8, reset_less=True)

    def elaborate(self, platform):
        m = Module()

        # Debug counter tick
        m.d.jtag += self.tck_cnt.eq(self.tck_cnt + 1)

        with m.FSM(domain="jtag", name="jtagtap") as self.fsm:
            with m.State("test_logic_reset"):
                with m.If(~self.tms):
                    m.next = "run_test_idle"
            with m.State("run_test_idle"):
                 with m.If( self.tms):
                     m.next = "select_dr_scan"
            # DR
            with m.State("select_dr_scan"):
                with m.If(~self.tms):
                    m.next = "capture_dr"
                with m.Else():
                    m.next = "select_ir_scan"
            with m.State("capture_dr"):
                with m.If(~self.tms):
                    m.next = "shift_dr"
                with m.Else():
                    m.next = "exit1_dr"
            with m.State("shift_dr"):
                with m.If( self.tms):
                    m.next = "exit1_dr"
            with m.State("exit1_dr"):
                with m.If(~self.tms):
                    m.next = "pause_dr"
                with m.Else():
                    m.next = "update_dr"
            with m.State("pause_dr"):
                with m.If( self.tms):
                    m.next = "exit2_dr"
            with m.State("exit2_dr"):
                with m.If( self.tms):
                    m.next = "update_dr"
                with m.Else():
                    m.next = "shift_dr"
            with m.State("update_dr"):
                with m.If( self.tms):
                    m.next = "select_dr_scan"
                with m.Else():
                    m.next = "run_test_idle"

            # IR
            with m.State("select_ir_scan"):
                with m.If(~self.tms):
                    m.next = "capture_ir"
                with m.Else():
                    m.next = "test_logic_reset"
            with m.State("capture_ir"):
                with m.If(~self.tms):
                    m.next = "shift_ir"
                with m.Else():
                    m.next = "exit1_ir"
            with m.State("shift_ir"):
                with m.If( self.tms):
                    m.next = "exit1_ir"
            with m.State("exit1_ir"):
                with m.If(~self.tms):
                    m.next = "pause_ir"
                with m.Else():
                    m.next = "update_ir"
            with m.State("pause_ir"):
                with m.If( self.tms):
                    m.next = "exit2_ir"
            with m.State("exit2_ir"):
                with m.If( self.tms):
                    m.next = "update_ir"
                with m.Else():
                    m.next = "shift_ir"
            with m.State("update_ir"):
                with m.If( self.tms):
                    m.next = "select_dr_scan"
                with m.Else():
                    m.next = "test_logic_reset"

        return m

class AlteraJTAG(Elaboratable):
    def __init__(self, chain=1):
        self.reset   = Signal()
        self.capture = Signal()
        self.shift   = Signal()
        self.update  = Signal()
        #
        self.runtest = Signal()
        self.drck    = Signal()
        self.sel     = Signal()

        self.tck = Signal()
        self.tms = Signal()
        self.tdi = Signal()
        self.tdo = Signal()

        self.rtck = Signal()
        self.rtms = Signal()
        self.rtdi = Signal()
        self.rtdo = Signal()

        # inputs
        self.tdouser = Signal()

        # outputs
        self.tmsutap = Signal()
        self.tckutap = Signal()
        self.tdiutap = Signal()

        assert chain == 1

        # TAP FSM
        self.tap_fsm = JTAGTAPFSM(self.tms)

    def add_reserved_jtag_decls(self, platform):
        # platform.add_resources([
        #     Resource("altera_jtag_reserved", 0,
        #         Subsignal("altera_reserved_tms", Pins("altera_reserved_tms", dir="i")),
        #         Subsignal("altera_reserved_tck", Pins("altera_reserved_tck", dir="i")),
        #         Subsignal("altera_reserved_tdi", Pins("altera_reserved_tdi", dir="i")),
        #         Subsignal("altera_reserved_tdo", Pins("altera_reserved_tdo", dir="o")),
        # )])
        platform.add_resources([
            Resource("altera_reserved_tms", 0, Pins("altera_reserved_tms", dir="iv")),
            Resource("altera_reserved_tck", 0, Pins("altera_reserved_tck", dir="iv")),
            Resource("altera_reserved_tdi", 0, Pins("altera_reserved_tdi", dir="iv")),
            Resource("altera_reserved_tdo", 0, Pins("altera_reserved_tdo", dir="ov")),
        ])

    def get_reserved_jtag_pads(self, platform):
        # return platform.request("altera_jtag_reserved")
        tms = platform.request("altera_reserved_tms")
        tms.fields["iv"].name = "altera_reserved_tms"
        tck = platform.request("altera_reserved_tck")
        tck.fields["iv"].name = "altera_reserved_tck"
        tdi = platform.request("altera_reserved_tdi")
        tdi.fields["iv"].name = "altera_reserved_tdi"
        tdo = platform.request("altera_reserved_tdo")
        tdo.fields["ov"].name = "altera_reserved_tdo"
        class JTAGPads:
            def __init__(self, tms, tck, tdi, tdo):
                self.altera_reserved_tms = tms
                self.altera_reserved_tck = tck
                self.altera_reserved_tdi = tdi
                self.altera_reserved_tdo = tdo
        reserved_jtag_pads = JTAGPads(tms.fields["iv"], tck.fields["iv"], tdi.fields["iv"], tdo.fields["ov"])
        # reserved_jtag_pads = Record([
        #         ('altera_reserved_tms', tms.fields["i"]),
        #         ('altera_reserved_tck', 1),
        #         ('altera_reserved_tdi', 1),
        #         ('altera_reserved_tdo', 1),
        #     ],
        #     name='altera_jtag_reserved',
        # )
        return reserved_jtag_pads

    def elaborate(self, platform):
        m = Module()

        self.add_reserved_jtag_decls(platform)
        self.reserved_pads = reserved_pads = self.get_reserved_jtag_pads(platform)

        m.domains.jtag = jtag = ClockDomain("jtag", reset_less=True)
        m.d.comb += [
            jtag.clk.eq(self.tck),
        ]


        m.domains.jtag_inv = jtag_inv = ClockDomain("jtag_inv", reset_less=True)
        m.d.comb += [
            jtag_inv.clk.eq(~jtag.clk),
        ]

        # m.submodules.tap_fsm = self.tap_fsm
        frag = Fragment.get(self.tap_fsm, platform)
        m.submodules.tap_fsm = frag
        m.d.jtag_inv += [
            self.reset.eq(self.tap_fsm.fsm.state == self.tap_fsm.fsm.encoding["test_logic_reset"]),
            self.capture.eq(self.tap_fsm.fsm.state == self.tap_fsm.fsm.encoding["capture_dr"]),
        ]

        if platform.device.lower().startswith("10m"):
            primitive = "fiftyfivenm_jtag"
        else:
            raise NotImplementedError("Unsupported Altera platform for JTAG")

        m.submodules.jtagblock = Instance(primitive,
            o_shiftuser      = self.shift,
            o_updateuser     = self.update,
            o_runidleuser    = self.runtest,
            o_clkdruser      = self.drck,
            o_usr1user       = self.sel,

            # Core interface
            i_tdouser = self.tdouser,
            o_tmsutap = self.tmsutap,
            o_tckutap = self.tckutap,
            o_tdiutap = self.tdiutap,

            # reserved pins
            i_tms = self.rtms,
            i_tck = self.rtck,
            i_tdi = self.rtdi,
            o_tdo = self.rtdo,
        )

        m.d.comb += [
            self.rtms.eq(reserved_pads.altera_reserved_tms),
            self.rtck.eq(reserved_pads.altera_reserved_tck),
            self.rtdi.eq(reserved_pads.altera_reserved_tdi),
            reserved_pads.altera_reserved_tdo.eq(self.rtdo),
        ]

        m.d.comb += [
            self.tck.eq(self.tckutap),
            self.tms.eq(self.tmsutap),
            self.tdi.eq(self.tdiutap),
        ]
        m.d.jtag_inv += self.tdouser.eq(self.tdo)

        return m

if __name__ == "__main__":
    from nmigen_boards.arrow_deca import ArrowDECAPlatform

    # topm = Module()
    # topm.domains.jtag = jtag = ClockDomain("jtag", reset_less=True)
    # tms = Signal()
    # topm.submodules.tapfsm = tapfsm = JTAGTAPFSM(tms)
    # main(topm, ports=[tms])
    platform = ArrowDECAPlatform()
    jtag = AlteraJTAG()
    jtag_frag = Fragment.get(jtag, platform)
    main(jtag_frag, ports=[jtag.rtms, jtag.rtck, jtag.rtdi, jtag.rtdo])
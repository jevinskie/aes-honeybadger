#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import Simulator, Delay, Settle

from aeshb.rom import ROM16x1

def test_rom16x1():
    m = Module()
    addr = Signal(4)
    m.submodules.rom = rom = ROM16x1(addr, init=0xAA55)

    sim = Simulator(m)

    def process():
        for i in range(16):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == ((rom.init >> i) & 1)

    sim.add_process(process)
    with sim.write_vcd("rom16x1.vcd", "rom16x1.gtkw", traces=rom.ports()):
        sim.run()


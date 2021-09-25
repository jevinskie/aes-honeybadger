#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import Simulator, Delay, Settle

from aeshb.rom import ROM16x1, ROM16x8

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


def test_rom16x8():
    m = Module()
    addr = Signal(4)
    static_random = bytes.fromhex("b2c8c5875fa45462afe35753b9b70f43")
    m.submodules.rom = rom = ROM16x8(addr, init=static_random)

    sim = Simulator(m)

    def process():
        for i in range(16):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == static_random[i]

    sim.add_process(process)
    with sim.write_vcd("rom16x8.vcd", "rom16x8.gtkw", traces=rom.ports()):
        sim.run()


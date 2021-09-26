#!/usr/bin/env python3
import random

from nmigen import *
from nmigen.sim import Simulator, Delay, Settle

from aeshb.rom import ROM16x1, ROM16x8, ROM16x16, ROM32x16, ROM128x16, ROM256x8
from aeshb.simpleaes import SimpleAES

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

def test_rom16x16():
    m = Module()
    addr = Signal(4)
    static_random = [34502, 10917, 31302, 39655, 62319, 3030, 62137, 43078,
                     56956, 59113, 7346, 65069, 22379, 6733, 4648, 4599]
    m.submodules.rom = rom = ROM16x16(addr, init=static_random)

    sim = Simulator(m)

    def process():
        for i in range(len(static_random)):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == static_random[i]

    sim.add_process(process)
    with sim.write_vcd("rom16x16.vcd", "rom16x16.gtkw", traces=rom.ports()):
        sim.run()

def test_rom32x16():
    m = Module()
    addr = Signal(5)
    # init = list(range(32))
    init = [random.randint(0, 2**16-1) for i in range(32)]
    m.submodules.rom = rom = ROM32x16(addr, init=init)

    sim = Simulator(m)

    def process():
        for i in range(len(init)):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == init[i]

    sim.add_process(process)
    with sim.write_vcd("rom32x16.vcd", "rom32x16.gtkw", traces=rom.ports()):
        sim.run()

def test_rom128x16():
    m = Module()
    addr = Signal(6)
    init = list(range(128))
    m.submodules.rom = rom = ROM128x16(addr, init=init)

    sim = Simulator(m)

    def process():
        for i in range(len(init)):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == init[i]

    sim.add_process(process)
    with sim.write_vcd("rom128x16.vcd", "rom128x16.gtkw", traces=rom.ports()):
        sim.run()

def test_rom256x8():
    m = Module()
    addr = Signal(8)
    m.submodules.rom = rom = ROM256x8(addr, init=SimpleAES.sbox)

    sim = Simulator(m)

    def process():
        for i in range(len(SimpleAES.sbox)):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()
            data = yield rom.data
            assert data == SimpleAES.sbox[i]

    sim.add_process(process)
    with sim.write_vcd("rom256x8.vcd", "rom256x8.gtkw", traces=rom.ports()):
        sim.run()

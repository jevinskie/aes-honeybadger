#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import Simulator, Delay, Settle

from aeshb.rom import ROM16x1

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
    m = Module()
    addr = Signal(4)
    m.submodules.rom = rom = ROM16x1(addr, init=0xAA55)

    sim = Simulator(m)

    def process():
        for i in range(16):
            yield addr.eq(i)
            yield Delay(1e-6)
            yield Settle()

    sim.add_process(process) # or sim.add_sync_process(process), see below
    with sim.write_vcd("rom16x1.vcd", "rom16x1.gtkw", traces=rom.ports()):
        sim.run()

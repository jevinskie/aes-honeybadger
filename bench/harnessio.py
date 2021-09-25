#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

class HarnessIO(Elaboratable):
    def __init__(self, sclk, copi, cipo, inputs, outputs):
        self.sclk = sclk
        self.copi = copi
        self.cipo = cipo
        self.inputs = inputs
        self.outputs = outputs
        self.input = Cat(*self.inputs)
        self.output = Cat(*self.outputs)

    def elaborate(self, platform):
        m = Module()
        return m



if __name__ == "__main__":
    sclk = Signal()
    copi = Signal()
    cipo = Signal()
    i0 = Signal()
    i1 = Signal(8)
    i2a = Signal(4)
    i2b = Signal(4)
    i2 = Cat(i2a, i2b)
    o0 = Signal()
    o1 = Signal(8)
    o2a = Signal(4)
    o2b = Signal(4)
    o2 = Cat(o2a, o2b)
    hio = HarnessIO(sclk, copi, cipo, inputs=[i0, i1, i2], outputs=[o0, o1, o2])
    main(hio, ports=[sclk, copi, cipo])

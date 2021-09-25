#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

class HarnessIO(Elaboratable):
    def __init__(self, sclk, copi, cipo, load, inputs, outputs):
        self.sclk = sclk
        self.copi = copi
        self.cipo = cipo
        self.load = load
        self.inputs = inputs
        self.outputs = outputs
        self.input = Cat(*self.inputs)
        self.output = Cat(*self.outputs)
        ilen = len(self.input)
        olen = len(self.output)
        self.input_scan = Signal(ilen, reset_less=True)
        self.input_latch = Signal(ilen, reset_less=True)
        self.input_buf = Signal(ilen, reset_less=True)
        self.output_buf = Signal(olen, reset_less=True)
        self.output_scan = Signal(olen, reset_less=True)

    def elaborate(self, platform):
        spi = ClockDomain(reset_less=True)
        m = Module()
        m.domains += spi
        m.d.comb += spi.clk.eq(self.sclk)
        m.d.spi += self.input_scan.eq(Cat(self.copi, *self.input_scan[:-1]))
        m.d.spi += self.output_scan.eq(Cat(*self.output_scan[1:], self.input_scan[-1]))
        m.d.comb += self.cipo.eq(self.output_scan[0])

        m.d.sync += self.input_buf.eq(self.input_latch)
        m.d.comb += self.input.eq(self.input_buf)
        m.d.sync += self.output_buf.eq(self.output)

        with m.If(self.load):
            m.d.spi += [
                self.input_latch.eq(self.input_scan),
                self.output_scan.eq(self.output_buf),
            ]

        return m



if __name__ == "__main__":
    sclk = Signal()
    copi = Signal()
    cipo = Signal()
    load = Signal()
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
    hio = HarnessIO(sclk, copi, cipo, load, inputs=[i0, i1, i2], outputs=[o0, o1, o2])
    main(hio, ports=[sclk, copi, cipo, load])

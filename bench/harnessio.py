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

    # lut4 = datad ? ( datac ? ( datab ? ( dataa ? mask[15] : mask[14])
    #                                  : ( dataa ? mask[13] : mask[12]))
    #                        : ( datab ? ( dataa ? mask[11] : mask[10])
    #                                  : ( dataa ? mask[ 9] : mask[ 8])))
    #              : ( datac ? ( datab ? ( dataa ? mask[ 7] : mask[ 6])
    #                                  : ( dataa ? mask[ 5] : mask[ 4]))
    #                        : ( datab ? ( dataa ? mask[ 3] : mask[ 2])
    #                                  : ( dataa ? mask[ 1] : mask[ 0])));

    @classmethod
    def simulate(cls, d0, d1, d2, d3, mask):
        if d3:
            if d2:
                if d1:
                    if d0:
                        return mask[15]
                    else:
                        return mask[14]
                else:
                    if d0:
                        return mask[13]
                    else:
                        return mask[12]
            else:
                if d1:
                    if d0:
                        return mask[11]
                    else:
                        return mask[10]
                else:
                    if d0:
                        return mask[9]
                    else:
                        return mask[8]
        else:
            if d2:
                if d1:
                    if d0:
                        return mask[7]
                    else:
                        return mask[6]
                else:
                    if d0:
                        return mask[5]
                    else:
                        return mask[4]
            else:
                if d1:
                    if d0:
                        return mask[3]
                    else:
                        return mask[2]
                else:
                    if d0:
                        return mask[1]
                    else:
                        return mask[0]

        return 0

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

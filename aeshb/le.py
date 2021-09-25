#!/usr/bin/env python3

from nmigen import *
from nmigen.cli import main

class LELUT4(Elaboratable):
    def __init__(self, d0, d1, d2, d3):
        self.d = Cat(d0, d1, d2, d3)
        self.combout = Signal()

    def elaborate(self, platform):
        m = Module()
        m.d.comb += self.combout.eq(self.d[0] ^ self.d[1] ^ self.d[2] ^ self.d[3])
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

if __name__ == "__main__":
    d0 = Signal()
    d1 = Signal()
    d2 = Signal()
    d3 = Signal()
    lelut4 = LELUT4(d0, d1, d2, d3)
    main(lelut4, ports=[d0, d1, d2, d3, lelut4.combout])

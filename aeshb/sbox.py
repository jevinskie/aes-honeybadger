#
# This file is part of LiteX.
#
# Copyright (c) 2013-2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from .simpleaes import SimpleAES

# Identifier ---------------------------------------------------------------------------------------

class SBoxROMLUT(Module):
    def __init__(self, in_byte: Signal):
        assert len(in_byte) == 8
        self.in_byte = in_byte
        self.out_byte = Signal(8)
        def next_pow2(x):
            return 1 << (x - 1).bit_length()
        self.mem = Memory(8, next_pow2(len(SimpleAES.sbox)), init=SimpleAES.sbox)
        self.specials += self.mem
        self.rd_port = self.mem.get_port(write_capable=False, async_read=False, has_re=False)
        self.specials += self.rd_port
        self.addr = Signal()
        self.comb += self.addr.eq(in_byte)
        self.comb += self.rd_port.adr.eq(self.addr)
        self.comb += self.out_byte.eq(self.rd_port.dat_r)

    def get_memories(self):
        return [(True, self.mem)]

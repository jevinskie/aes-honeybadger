#!/usr/bin/env python3

from collections import OrderedDict
import enum
from typing import Final

from rich import print

from pyftdi.jtag import *

# import ctypes.macholib.dyld
# ctypes.macholib.dyld.DEFAULT_LIBRARY_FALLBACK.append('/opt/brew/lib')
# ctypes.macholib.dyld.DEFAULT_LIBRARY_FALLBACK.append('/opt/homebrew/lib')
# ctypes.macholib.dyld.DEFAULT_LIBRARY_FALLBACK.append('/opt/homebrew-x86/lib')
import usb.core
import usb.util
from usb._objfinalizer import AutoFinalizedObject

from intervaltree import Interval, IntervalTree

import attr

from bitfield import *

VID: Final[int] = 0x09fb
PID: Final[int] = 0x6010
PID_FX2LP: Final[int] = 0x6810



class BBit(enum.IntEnum):
    BYTE_SHIFT: Final[int] = (1 << 7)
    READ:       Final[int] = (1 << 6)
    LED:        Final[int] = (1 << 5)
    TDI:        Final[int] = (1 << 4)
    NCS:        Final[int] = (1 << 3)
    NCE:        Final[int] = (1 << 2)
    TMS:        Final[int] = (1 << 1)
    TCK:        Final[int] = (1 << 0)

class BlasterByte(BitFieldUnion):
    byte_shift = BitField(7, 1)
    read       = BitField(6, 1)
    led        = BitField(5, 1)
    tdi        = BitField(4, 1)
    ncs        = BitField(3, 1)
    nce        = BitField(2, 1)
    tms        = BitField(1, 1)
    tck        = BitField(0, 1)
    nbytes     = BitField(0, 6)



@attr.s()
class FX2LP:
    _dev = attr.ib(init=False, default=usb.core.find(idVendor=VID, idProduct=PID_FX2LP))

    class CtrlReqType(enum.IntEnum):
        FW_LOAD: Final[int] = 0xA0

    def __attrs_post_init__(self):
        self._dev.reset()
        self._dev.set_configuration()

    def read_raw(self, addr: int, sz: int) -> bytes:
        assert 0 <= addr < 2**16
        assert 0 <= sz < 0x1000
        buf = self._dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_INTERFACE | usb.util.CTRL_IN,
                                      self.CtrlReqType.FW_LOAD, addr, 0, sz)
        buf = bytes(buf)
        return buf
        pass

    def write_raw(self, addr: int, buf: bytes) -> None:
        assert 0 <= addr < 2**16
        assert len(buf) < 0x1000
        self._dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_INTERFACE | usb.util.CTRL_OUT,
                                      self.CtrlReqType.FW_LOAD, addr, 0, buf)

    def read(self, addr: int, sz: int) -> bytes:
        assert 0 <= addr < 2**16
        assert 0 <= sz < 0x1000
        return self.read_raw(addr, sz)

    def write(self, addr: int, buf: bytes) -> None:
        assert 0 <= addr < 2**16
        nbytes = len(buf)
        while nbytes > 0:
            self.write_raw(addr, buf)

    def hold_in_reset(self, hold_reset: bool) -> None:
        self.write(0xE600, bytes([hold_reset]))

    @classmethod
    def read_ihex(cls, ihex_path) -> OrderedDict:
        mem = IntervalTree()
        with open(ihex_path) as f:
            for l in map(lambda l: l.strip(), f):
                if l[0] != ":":
                    continue
                nbytes = int(l[1:1+2], 16)
                addr = int(l[3:3+4], 16)
                rty = int(l[7:7+2], 16)
                buf = bytes.fromhex(l[9:-2])
                checksum = int(l[-2:], 16)
                assert len(buf) == nbytes
                if rty == 1:
                    break
                else:
                    assert rty == 0
                assert len(buf) > 0
                mem[addr:addr+len(buf)] = buf
        # mem.merge_neighbors(distance=0, data_reducer=lambda cd, nd: cd + nd)
        mem_dict = OrderedDict()
        for i in sorted(mem, key=lambda i: i.begin):
            mem_dict[i.begin] = i.data
        return mem_dict

    def send_ihex(self, ihex_path) -> None:
        self.hold_in_reset(True)

        mem = self.read_ihex(ihex_path)
        for addr, buf in mem.items():
            self.write(addr, buf)

        self.hold_in_reset(False)



@attr.s()
class USBBlaster2(AutoFinalizedObject):
    _dev = attr.ib(init=False, default=usb.core.find(idVendor=VID, idProduct=PID))
    _cfg = attr.ib(init=False)
    _intf = attr.ib(init=False)
    _epo = attr.ib(init=False)
    _epi = attr.ib(init=False)
    _last_tms = attr.ib(init=False)
    _last_tdi = attr.ib(init=False)

    class CtrlReqType(enum.IntEnum):
        GET_READ_REV: Final[int] = 0x94

    def __attrs_post_init__(self):
        self._dev.reset()
        self._dev.set_configuration()
        self._cfg = self._dev.get_active_configuration()
        self._intf = self._cfg[(0,0)]

        self._epo = usb.util.find_descriptor(
            self._intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        assert self._epo is not None

        self._epi = usb.util.find_descriptor(
            self._intf,
            # match the first IN endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)
        assert self._epi is not None

        self.revision = self.get_revision()
        print(f"revision: {self.revision}")
        self._last_tms = None
        self._last_tdi = None

    def _finalize_object(self):
        self.flush()

    def flush(self):
        self._epo.write(bytes(64))

    def get_revision(self):
        rev = self._dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_INTERFACE | usb.util.CTRL_IN,
                                      self.CtrlReqType.GET_READ_REV, 0, 0, 5)
        rev = bytes(rev).decode().rstrip("\0")
        return rev

    def tick_tms(self, b):
        bl, bh = self.make_clock_bytes(self.make_byte(b, self._last_tdi))
        r = self._epo.write(bytes([bl, bh]))
        print(f"tick_tms r: {r}")
        self._last_tms = b

    def tick_tdo(self, nbits):
        bl = self.make_byte(self._last_tms, self._last_tdi)
        bh = bl | BBit.TCK | BBit.READ
        obuf = bytes([bl, bh] * nbits) + bytes([0x5f])  # flush w/ 5f
        self._epo.write(obuf)
        ibuf = self._epi.read(512)
        print(f"ibuf: len: {len(ibuf)} {ibuf}")
        bsin = "".join(map(str, [b & 1 for b in ibuf]))
        print(f"bsin: {bsin}")
        bs = BitSequence(bsin)
        print(f"bs: {bs}")
        return bs

    def tick_tdi(self, bout):
        obuf = bytes()
        for b in bout:
            bl = self.make_byte(self._last_tms, b)
            bh = bl | BBit.TCK
            self._last_tdi = b
            obuf += bytes([bl, bh])
        print(f"ticking tdi with {len(obuf)} {obuf.hex()}")
        r = self._epo.write(obuf)
        print(f"tdi r: {r}")

    def tick_tdi_with_tdo(self, bout):
        obuf = bytes()
        for b in bout:
            bl = self.make_byte(self._last_tms, b)
            bh = bl | BBit.TCK | BBit.READ
            self._last_tdi = b
            obuf += bytes([bl, bh])
        # obuf += bytes([0x5f])
        print(f"ticking tdi with {len(obuf)} {obuf.hex()}")
        r = self._epo.write(obuf)
        print(f"tdi r: {r}")
        # ibuf = self._epi.read(512)
        # bsin = "".join(map(str, [b & 1 for b in ibuf]))
        # print(f"bsin: {bsin}")
        # bs = BitSequence(bsin)
        # print(f"bs: {bs}")
        # return bs

    def read_from_buffer(self, sz):
        self._epo.write(bytes([0x5f]))
        ibuf = self._epi.read(512)
        print(f"read_from_buffer len: {len(ibuf)}")
        bsin = "".join(map(str, [b & 1 for b in ibuf]))
        print(f"bsin: {bsin}")
        bs = BitSequence(bsin)
        print(f"bs: {bs}")
        return bs


    @classmethod
    def make_byte(cls, tms, tdi, read=False):
        b = BBit.LED
        if read:
            b |= BBit.READ
        if tms:
            b |= BBit.TMS
        if tdi:
            b |= BBit.TDI
        return b

    @classmethod
    def make_clock_bytes(cls, b):
        return b, b | BBit.TCK


class BlasterJTAGController(JtagController):
    def __init__(self):
        self.blaster = USBBlaster2()

    def configure(self, url: str) -> None:
        raise NotImplementedError

    def close(self, freeze: bool = False) -> None:
        del self.blaster

    def purge(self) -> None:
        raise NotImplementedError

    def reset(self, sync: bool = False) -> None:
        self.write_tms(BitSequence('11111'))

    def sync(self) -> None:
        raise NotImplementedError

    def write_tms(self, tms: BitSequence,
                  should_read: bool = False) -> None:
        print(f'write_tms(should_read={should_read}) with {tms}')
        for b in tms:
            self.blaster.tick_tms(b)

    def read(self, length: int) -> BitSequence:
        print(f'read({length})')
        tdo = self.blaster.tick_tdo(length)
        return tdo

    def write(self, out: Union[BitSequence, str], use_last: bool = True):
        print(f'write(use_last={use_last}) with {out}')
        self.blaster.tick_tdi(out)


    def write_with_read(self, out: BitSequence,
                        use_last: bool = False) -> int:
        if use_last:
            raise NotImplementedError
        self.blaster.tick_tdi_with_tdo(out)

    def read_from_buffer(self, length) -> BitSequence:
        bs = self.blaster.read_from_buffer(length)
        return bs


def blaster_test():
    # blaster = USBBlaster2()
    # print(blaster)
    ctrl = BlasterJTAGController()
    print(ctrl)
    engine = JtagEngine(ctrl=ctrl)
    engine.reset()
    print(engine)
    tool = JtagTool(engine)
    print(tool)

    # engine.change_state("shift_ir")
    # engine.change_state("test_logic_reset")
    # engine.change_state("run_test_idle")
    # engine.change_state("capture")
    # r = tool.detect_register_size()
    # print(f"register size: {r}")
    # r = tool.idcode()
    # print(f"idcode: {r}")

    engine.reset()

    # engine.write_ir(BitSequence('0000000110', msb=True))
    engine.write_ir(BitSequence('0000000110', msb=True, length=10))
    r = engine.read_dr(32)
    print(r)
    print(r.tobytes().hex())


def fx2_test():
    fx2 = FX2LP()
    print(fx2)
    fx2.send_ihex('blaster_6810.hex')


def main():
    # blaster_test()
    fx2_test()

if __name__ == "__main__":
    main()

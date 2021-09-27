#!/usr/bin/env python3

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
# from usb._objfinalizer import AutoFinalizedObject

import attr

VID: Final[int] = 0x09fb
PID: Final[int] = 0x6010

class CtrlReqType(enum.IntEnum):
    GET_READ_REV:  Final[int] = 0x94

@attr.s()
class USBBlaster2:
    _dev = attr.ib(init=False, default=usb.core.find(idVendor=VID, idProduct=PID))
    _cfg = attr.ib(init=False)
    _intf = attr.ib(init=False)
    _epo = attr.ib(init=False)
    _epi = attr.ib(init=False)

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

    def get_revision(self):
        rev = self._dev.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_INTERFACE | usb.util.CTRL_IN,
                                      CtrlReqType.GET_READ_REV, 0, 0, 5)
        rev = bytes(rev).decode().rstrip("\0")
        return rev

    @classmethod
    def make_byte(cls, tms, tdi):
        pass

    def spam(self):
        self._epo.write(bytes([2, 3]*16 + [0] * 48))
        obuf = bytes([(1<<6)|0, (1<<6)|1] * 16)
        print(obuf.hex())
        print(len(obuf))
        # obuf += bytes(64-len(obuf))
        print(obuf.hex())
        print(len(obuf))
        r = self._epo.write(obuf + bytes([0x5f]))
        # r = self._epo.write(bytes.fromhex('c7efbeadde0000005f004100415f'))
        self._epo.write(bytes(64))
        print(f"write res: {r}")
        # r = self._epo.write(bytes([0x5f]))
        r = self._epi.read(64)
        print(f"read res: {r}, len: {len(r)}")
        if len(r) != 64:
            print(f"warning got unexpected length")

    def read(self, sz):
        return self.xfer(b'\x00' * sz)

    def write(self, buf):
        self.xfer(buf)
        return

    def xfer(self, buf):
        return_int = False
        if isinstance(buf, str):
            buf = bytes.fromhex(buf)
        if isinstance(buf, int) and 0 <= buf <= 0xff:
            buf = bytes([buf])
            return_int = True
        assert len(buf) < 60 # FIXME: HACK
        self._epo.write(buf)
        ret = bytes(self._epi.read(len(buf)))
        if return_int:
            ret = ret[0]
        return ret


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
        raise NotImplementedError

    def sync(self) -> None:
        raise NotImplementedError

    def write_tms(self, tms: BitSequence,
                  should_read: bool=False) -> None:
        self.p(f'write_tms(should_read={should_read}) with {tms}')
        for b in tms:
            tick_tms_ext(self.dut, b)

    def read(self, length: int) -> BitSequence:
        self.p(f'read({length})')
        tdo = tick_tdo_ext(self.dut, length)
        return tdo

    def write(self, out: Union[BitSequence, str], use_last: bool = True):
        self.p(f'write(use_last={use_last}) with {out}')
        tick_tdi_ext(self.dut, out)


    def write_with_read(self, out: BitSequence,
                        use_last: bool = False) -> int:
        raise NotImplementedError

    def read_from_buffer(self, length) -> BitSequence:
        raise NotImplementedError


def main():
    blaster = USBBlaster2()
    print(blaster)
    blaster.spam()

if __name__ == "__main__":
    main()

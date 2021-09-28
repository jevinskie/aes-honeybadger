import collections
from typing import Final, Optional

# https://docs.python.org/3/howto/descriptor.html#properties
class Property:
    "Emulate PyProperty_Type() in Objects/descrobject.c"

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)

# https://www.colmryan.org/posts/bitfield-nicieties-in-python/

class BitFieldInt(int):
    _offset: Final[int]
    _width: Final[int]
    _name: Final[Optional[str]]
    _bf: 'BitField'

    def __new__(cls, bf: 'BitField', value: int, offset: int, width: int = 1, name: Optional[str] = None):
        if not isinstance(value, int):
            raise TypeError("data must be an int")
        uint_max = (1 << width) - 1
        uint_min = 0
        if value > uint_max:
            raise ValueError(f'{cls.__name__} cannot be > 2**{width}-1 {uint_max:#x} {uint_max:d}. Given: {value:#x} {value:d}')
        if value < 0:
            raise ValueError(f'{cls.__name__} cannot be < 0. Given: {value:#x} {value:d}')
        rval = int.__new__(cls, value)
        rval._offset = offset
        rval._width = width
        rval._name = name
        rval._bf = bf
        return rval

    def __repr__(self):
        return f'{self.__class__.__name__}<{self._name}>({int(self)})'


    def __get__(self, obj, objtype=None):
        print(f'BitFieldInt __get__ obj: {obj} objtype: {objtype}')
        res = super().__get__(obj, objtype)
        # print(f'res: {res}')
        return res

    def __set__(self, obj, value):
        print(f'BitFieldInt __set__ obj: {obj} value: {value}')
        # su = super()
        # res = su.__set__(obj, value)
        res = value
        # print(f'res: {res}')
        return res

    @Property
    def bf(self):
        return self._bf

    @Property
    def union(self):
        return self.bf.union

    @Property
    def name(self):
        return self._name

    n = name

    @Property
    def offset(self):
        return self._offset

    o = offset

    @Property
    def width(self):
        return self._width

    w = width

    @Property
    def mask(self):
        # print(f'BitFieldInt get mask')
        return (1 << self.width) - 1

    m = mask

    @Property
    def shifted_mask(self):
        # print(f'BitFieldInt get shifted_mask')
        return self.mask << self.offset

    sm = shifted_mask

# AlexAltea's ntypes style
def BitFieldInt_type(bf: 'BitField', offset: int, width: int = 1, name: Optional[str] = None):
    cls_name = f'BitFieldInt_o_{offset}_w_{width}'
    if name is not None:
        cls_name += f'_{name}'
    def __new__(cls, value):
        return BitFieldInt.__new__(cls, bf, value, offset, width, cls_name)

    r = type(cls_name, (BitFieldInt,), {
        "__new__": __new__,
        "__repr__": lambda self: f'{self.__class__.__name__}{{{self.offset},{self.width}}}({int(self)})'
    })
    return r


class BitField:
    """Bit field in a bit field union"""
    def __init__(self, offset: int, width: int = 1, name: Optional[str] = None, union: Optional['BitFieldUnion'] = None):
        super().__init__()
        self._offset = offset
        self._width = width
        self._name = name
        self._union = union

    @Property
    def union(self):
        return self._union

    u = union

    @Property
    def name(self):
        return self._name

    n = name

    @Property
    def offset(self):
        return self._offset

    o = offset

    @Property
    def width(self):
        return self._width

    w = width

    @Property
    def mask(self):
        print(f'BitField get mask')
        return (1 << self.width) - 1

    m = mask

    @Property
    def shifted_mask(self):
        print(f'BitField get shifted_mask')
        return self.mask << self.offset

    sm = shifted_mask

class BitFieldProperty:
    offset: int
    width: int

    def __init__(self, parent_name: str, parent: 'BitFieldUnion', bf: BitField, name: str, fget=None, fset=None, fdel=None, doc=None):
        self.parent_name = parent_name
        self.parent = parent
        self.bf = bf
        self.name = name
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.offset = bf.offset
        self.width = bf.width
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            # FIXME
            # return self
            packed = 0
        else:
            packed = obj.packed
        bf = self.bf
        v = (packed >> bf.offset) & (2 ** bf.width - 1)
        r = BitFieldInt(bf, v, bf.offset, bf.width, bf.name)
        return r

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)


class BitFieldUnionMeta(type):
    """Metaclass for injecting bitfield descriptors"""
    @classmethod
    def __prepare__(metacls, name, bases):
        return collections.OrderedDict()

    def __init__(self, name, bases, dct):
        type.__init__(self, name, bases, dct)
        self.packed = 0
        self.packed_fields = []
        for k, v in dct.items():
            if isinstance(v, BitField):
                def fget(self, offset=v.offset, width=v.width):
                    return (self.packed >> offset) & (2**width-1)

                def fset(self, val, offset=v.offset, width=v.width):
                    # check we don't exceed the width of the field
                    if (val & (2**width-1)) != val:
                        err_msg = f'attempted to assign value that does not fit in bit field width {width}'
                        raise ValueError(err_msg)
                    self.packed &= ~((2**width-1) << offset) # clear the field
                    self.packed |= (val & (2**width-1)) << offset # set the field

                bf_name = k
                bf = v
                bf._name = bf_name
                bf._union = self
                parent_name = name
                parent = self
                self.packed_fields.append(bf_name)
                setattr(self, k, BitFieldProperty(parent_name, parent, bf, bf_name, fget, fset, None, None))


class BitFieldUnion(metaclass=BitFieldUnionMeta):
    def __init__(self, **kwargs):
        super().__init__()
        if 'packed' in kwargs and len(kwargs) > 1:
            raise AttributeError('unable to set both `packed` aggregate and another bit field called `packed`')
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        hdr = f'<{self.__class__.__name__} ==> {self.packed:#04x}'
        ftr = '>'
        fbfs = []
        if len(self.packed_fields):
            hdr += '\n'
            longest_name_len = max(map(len, self.packed_fields))
            for bf_name in self.packed_fields:
                v = self.__getattribute__(bf_name)
                if v.width == 1:
                    fbfs.append(f"\t{bf_name:>{longest_name_len}}[{v.offset:2}]    => {bool(v)}")
                else:
                    fbfs.append(f"\t{bf_name:>{longest_name_len}}[{v.offset+v.width-1:2}:{v.offset:2}] => {v:#06x} {v:d} {v:#0{2+v.width}b}")
            return (
                hdr +
                '\n'.join(fbfs) +
                ftr
            )
        else:
            return hdr + ftr

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.packed == other.packed

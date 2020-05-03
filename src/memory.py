from __future__ import annotations

import attr
from ctypes import c_int8


@attr.s(eq=False, order=False, repr=False)
class Byte:
    pointer: c_int8 = attr.ib(converter=c_int8)
    first_nibble: int = attr.ib(init=False)
    second_nibble: int = attr.ib(init=False)

    @first_nibble.default
    def first_nibble_default(self) -> int:
        val = self.pointer.value
        if self.pointer.value < 0:
            val = 0xFF + self.pointer.value

        return val >> 4

    @second_nibble.default
    def second_nibble_default(self) -> int:
        return self.pointer.value & 0x0F

    @property
    def value(self):
        return self.pointer.value

    @value.setter
    def value(self, value):
        self.pointer.value = value

    def __str__(self):
        return f"{self.pointer.value}"

    def __repr__(self):
        return f"Byte(value={self.value}, first_nibble={self.first_nibble}, second_nibble={self.second_nibble})"

    def __format__(self, fmt_spec):
        data = self.pointer.value
        if self.pointer.value < 0:
            data = self.first_nibble * 0x10 + self.second_nibble
        if fmt_spec.lower().endswith("b"):
            return f"{data:08b}"
        if fmt_spec.lower().endswith("x"):
            return f"{data:02X}"
        else:
            return self.__repr__()

    def __abs__(self):
        return abs(self.value)

    def __add__(self, other):
        if type(other) is Byte:
            return Byte(self.value + other.value)
        return Byte(self.value + other)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if type(other) is Byte:
            return Byte(self.value - other.value)
        return Byte(self.pointer.value - other)

    def __rsub__(self, other):
        return Byte(other - self.pointer.value)

    def __mul__(self, other):
        if type(other) is Byte:
            return Byte(self.value * other.value)
        return Byte(self.pointer.value * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if type(other) is Byte:
            return Byte(self.value // other.value)
        return Byte(self.pointer.value // other)

    def __rtruediv__(self, other):
        return Byte(other // self.pointer.value)

    def __floordiv__(self, other):
        if type(other) is Byte:
            return Byte(self.value // other.value)
        return self.__truediv__(other)

    def __rfloordiv__(self, other):
        return self.__rtruediv__(other)

    def __lshift__(self, other):
        return Byte(self.pointer.value << other)

    def __rshift__(self, other):
        return Byte(self.pointer.value >> other)

    def __eq__(self, other):
        return self.pointer.value == other

    def __lt__(self, other):
        return self.pointer.value < other

    def __gt__(self, other):
        return self.pointer.value > other

    def __le__(self, other):
        return self.pointer.value <= other

    def __ge__(self, other):
        return self.pointer.value <= other

    @classmethod
    def from_hex(cls, hex: str) -> Byte:
        val = int(hex, 16)
        instance = cls(val)
        return instance


@attr.s(repr=False)
class Word:
    first_byte: Byte = attr.ib(validator=attr.validators.instance_of(Byte))
    second_byte: Byte = attr.ib(validator=attr.validators.instance_of(Byte))

    def __iter__(self):
        return iter(attr.astuple(self, recurse=False))

    def __repr__(self):
        return f"Word({self.first_byte.value:02X}{self.second_byte.value:02X})"


class Memory:
    def __init__(self):
        self.memory = [Byte(0)] * 4096

    @classmethod
    def from_list(cls, data):
        if len(data) != 4096:
            raise ValueError
        instance = cls()
        instance.memory = [Byte(i) for i in data]
        return instance

    def __getitem__(self, slice: slice):
        return self.memory[slice]

    def __setitem__(self, key, val):
        self.memory[key] = val

    def __iter__(self):
        return iter(self.memory)

    def __len__(self):
        return len(self.memory)


if __name__ == "__main__":
    mem = Memory()

from __future__ import annotations

import attr


@attr.s
class Byte:
    value: int = attr.ib()
    first_nibble: int = attr.ib(init=False)
    second_nibble: int = attr.ib(init=False)

    @value.validator
    def value_validator(self, attribute, value):
        if value < 0 or value > 255:
            raise ValueError("A Byte's value must be between 0 and 255")

    @first_nibble.default
    def first_nibble_default(self) -> int:
        return self.value >> 4

    @second_nibble.default
    def second_nibble_default(self) -> int:
        return self.value & 0x0F

    def __str__(self):
        return f"{self.value:02X}"

    @classmethod
    def from_hex(cls, hex: str) -> Byte:
        val = int(hex, 16)
        instance = cls(val)
        return instance


@attr.s
class Word:
    first_byte: Byte = attr.ib(validator=attr.validators.instance_of(Byte))
    second_byte: Byte = attr.ib(validator=attr.validators.instance_of(Byte))

    def __iter__(self):
        return iter(attr.astuple(self, recurse=False))

    def __str__(self):
        return f"{self.first_byte.value:02X}{self.second_byte.value:02X}"


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

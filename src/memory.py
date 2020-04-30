from __future__ import annotations

from pathlib import Path

import attr
import numpy as np
from loguru import logger


@attr.s
class Byte:
    value: np.uint8 = attr.ib(
        default=np.uint8(0),
        validator=attr.validators.instance_of(np.uint8),
        converter=np.uint8,
    )
    first_nibble: np.uint8 = attr.ib(validator=attr.validators.instance_of(np.uint8))
    second_nibble: np.uint8 = attr.ib(validator=attr.validators.instance_of(np.uint8))

    @first_nibble.default
    def first_nibble_default(self) -> int:
        return np.uint8(self.value >> 4)

    @second_nibble.default
    def second_nibble_default(self) -> int:
        return np.uint8(self.value & 0x0F)

    def __str__(self):
        return f"{self.value:02x}"

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
        return f"{self.first_byte.value:02x}{self.second_byte.value:02x}"


class Memory:
    def __init__(self):
        self.memory = [Byte(0)] * 4096

    def __getitem__(self, slice: slice):
        return self.memory[slice]

    def __setitem__(self, key, val):
        self.memory[key] = val

    def load(self, program_path: str, initial_position: int) -> None:
        # This function assumes the data is a binary blob
        logger.debug(f"Loading program: {program_path}")
        with open(program_path, "rb") as f:
            data = f.read()

        if initial_position + len(data) >= len(self.memory):
            logger.warning("Trying to load a program that will not fit in memory")
            logger.warning("Memory size: 4096")
            logger.warning(f"Program's initial position: {initial_position}")
            logger.warning(f"Program's length: {len(data)} bytes")
            raise IndexError

        for offset, byte in enumerate(data):
            self.memory[initial_position + offset] = Byte(byte)


if __name__ == "__main__":
    mem = Memory()
    path = Path().resolve().parent.joinpath("data/zero_to_fifty.bin")
    mem.load(str(path), 0)

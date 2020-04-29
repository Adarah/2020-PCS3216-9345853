from __future__ import annotations

from pathlib import Path
from typing import List

import attr
from loguru import logger


@attr.dataclass
class Byte:
    value: int = attr.ib(default=0, converter=int)
    first_nibble: int = attr.ib()
    second_nibble: int = attr.ib()

    @value.validator
    def value_validator(self, _, value: int) -> None:
        if value < 0x00 or value > 0xFF:
            raise ValueError

    @first_nibble.default
    def first_nibble_default(self) -> int:
        return self.value >> 4

    @second_nibble.default
    def second_nibble_default(self) -> int:
        return self.value & 0x0F

    @classmethod
    def from_hex(cls, hex: str) -> Byte:
        val = int(hex, 16)
        instance = cls(val)
        return instance


class Memory:
    def __init__(self):
        self._memory = [Byte(0)] * 4096

    @property
    def memory(self) -> List[int]:
        return self._memory

    @memory.setter
    def memory(self, value: int, position: int) -> None:
        self.memory[position] = value

    def load(self, program_path: str, initial_position: int) -> None:
        # This function assumes the data is a binary blob
        logger.debug(f"Loading program: {program_path}")
        with open(program_path, "rb") as f:
            data = f.read()

        if initial_position + len(data) >= len(self.memory):
            logger.warning("Trying to load a program that will not fit in memory")
            logger.warning("Memory size: 4096")
            logger.warning(f"Program's initial position: {initial_position}")
            logger.warning(f"Program's length: {len(data)}")
            raise IndexError

        for offset, byte in enumerate(data):
            self.memory[initial_position + offset] = Byte(byte)


if __name__ == "__main__":
    mem = Memory()
    path = Path().resolve().parent.joinpath("data/zero_to_fifty.bin")
    mem.load(str(path), 0)

from loguru import logger

from src.memory import Memory, Byte
from pathlib import Path


class Loader:
    def __init__(self, memory: Memory):
        self.memory = memory

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
    loader = Loader(mem)
    path = Path().resolve().parent.joinpath("data/zero_to_fifty.bin")
    loader.load(str(path), 0)

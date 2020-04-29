from src.memory import Memory, Byte
from pathlib import Path
import pytest


def test_load():
    mem = Memory()
    path = str(Path().joinpath("data/zero_to_fifty.bin"))
    mem.load(path, 0)
    assert mem.memory == [Byte(i) if i < 50 else Byte(0) for i in range(4096)]
    with pytest.raises(IndexError):
        mem.load(path, 4080)


test_load()

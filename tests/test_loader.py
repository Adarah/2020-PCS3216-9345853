from pathlib import Path

import pytest

from src.loader import Loader
from src.memory import Byte, Memory


def test_load():
    mem = Memory()
    loader = Loader(mem)
    path = str(Path().joinpath("data/zero_to_fifty.bin"))
    loader.load(path, 0)
    assert mem.memory == [Byte(i) if i < 50 else Byte(0) for i in range(4096)]
    with pytest.raises(IndexError):
        loader.load(path, 4080)


test_load()

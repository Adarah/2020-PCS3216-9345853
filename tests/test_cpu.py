from pathlib import Path

import pytest

from src.cpu import CPU
from src.memory import Byte, Memory, Word


@pytest.fixture
def memory():
    mem = Memory()
    for i in range(4096):
        mem[i] = Byte(i % 256)

    path = Path().resolve().joinpath("data/test.bin")
    mem.load(path, 0)
    return mem


@pytest.fixture
def cpu(memory):
    cpu = CPU(memory)
    return cpu


def test_fetch(cpu):
    cpu.PC = 1024
    cpu.fetch()
    assert cpu.PC == 1026
    assert cpu.instruction == Word(Byte(0), Byte(1))
    cpu.fetch()
    assert cpu.PC == 1028
    assert cpu.instruction == Word(Byte(2), Byte(3))
    cpu.fetch()
    assert cpu.PC == 1030
    assert cpu.instruction == Word(Byte(4), Byte(5))

    cpu.PC = 4094
    cpu.fetch()
    assert cpu.PC == 4096
    assert cpu.instruction == Word(Byte(254), Byte(255))
    with pytest.raises(IndexError):
        cpu.fetch()


@pytest.mark.parametrize(
    "PC, opcode, arg",
    [
        (0, 0, 0x000),
        (2, 1, 0x234),
        (4, 2, 0x345),
        (6, 3, 0x456),
        (8, 4, 0x567),
        (10, 5, 0x678),
        (12, 6, 0x789),
        (14, 7, 0x89A),
        (16, 8, 0x9AB),
        (18, 9, 0xABC),
        (20, 10, 0xBCD),
        (22, 11, 0xCDE),
        (24, 12, 0xDEF),
        (26, 13, 0xEF0),
        (28, 14, 0xF01),
        (30, 15, 0x012),
    ],
)
def test_decode(cpu, PC, opcode, arg):
    cpu.PC = PC
    cpu.instruction = Word(*cpu.memory[cpu.PC : cpu.PC + 2])
    assert cpu.decode() == (cpu.opcode[opcode], arg)


@pytest.mark.parametrize("arg", [0x100, 0x300, 0x123, 0xFF3])
def test_jmp(cpu, arg):
    cpu.jmp(arg)
    assert cpu.PC == arg


@pytest.mark.parametrize(
    "AC, arg, expected_output",
    [(0, 0x100, 0x100), (1, 0x300, 0), (-3, 0x123, 0), (0, 0xFF3, 0xFF3)],
)
def test_jmp_if_zero(cpu, AC, arg, expected_output):
    cpu.AC = AC
    cpu.jmp_if_zero(arg)
    assert cpu.PC == expected_output


@pytest.mark.parametrize(
    "AC, arg, expected_output",
    [(0, 0x100, 0), (0.01, 0x300, 0), (-3, 0x123, 0x123), (-655555, 0xFF3, 0xFF3)],
)
def test_jmp_if_negative(cpu, AC, arg, expected_output):
    cpu.AC = AC
    cpu.jmp_if_negative(arg)
    assert cpu.PC == expected_output


@pytest.mark.parametrize("arg", [123, 0, -44, 67])
def test_load_value(cpu, arg):
    cpu.load_value(arg)
    assert cpu.AC == arg


@pytest.mark.parametrize("AC, arg", [(10, 0x334), (-33, 0x35), (3, 0x550), (0, 0xFF0)])
def test_add(cpu, AC, arg):
    cpu.AC = AC
    cpu.add(arg)
    assert cpu.AC == AC + (arg % 256)


@pytest.mark.parametrize("AC, arg", [(10, 0x334), (-33, 0x35), (3, 0x550), (0, 0xFF0)])
def test_subtract(cpu, AC, arg):
    cpu.AC = AC
    cpu.subtract(arg)
    assert cpu.AC == AC - (arg % 256)


@pytest.mark.parametrize("AC, arg", [(10, 0x334), (-33, 0x35), (3, 0x550), (0, 0xFF0)])
def test_multiply(cpu, AC, arg):
    cpu.AC = AC
    cpu.multiply(arg)
    assert cpu.AC == AC * (arg % 256)


@pytest.mark.parametrize("AC, arg", [(10, 256), (-33, 0x35), (0.3, 0x550), (0, 0xFF0)])
def test_divide(cpu, AC, arg):
    cpu.AC = AC
    if (arg % 256) == 0:
        with pytest.raises(ZeroDivisionError):
            cpu.divide(arg)
    else:
        cpu.divide(arg)
        assert cpu.AC == int(AC / (arg % 256))


@pytest.mark.parametrize("arg", [0x552, 0xF4A, 0x345, 0xBB3])
def test_load_from_memory(cpu, arg):
    cpu.load_from_memory(arg)
    assert cpu.AC == cpu.memory[arg].value


@pytest.mark.parametrize("AC, arg", [(10, 0x334), (0, 0x35), (0xFA, 0x550), (0, 0xFF0)])
def test_move_to_memory(cpu, AC, arg):
    cpu.AC = AC
    cpu.move_to_memory(arg)
    assert cpu.memory[arg] == Byte(AC)


@pytest.mark.parametrize(
    "PC, arg", [(0x123, 0x552), (0xF3A, 0xF4A), (0x00, 0x345), (0x9A, 0xBC3)]
)
def test_subroutine_call(cpu, PC, arg):
    cpu.PC = PC
    cpu.subroutine_call(arg)
    first_nibble = format(PC, "03x")[0]
    second_byte = format(PC, "03x")[1:]
    assert cpu.PC == arg + 2
    assert cpu.memory[arg] == Byte(int(first_nibble, base=16))
    assert cpu.memory[arg + 1] == Byte(int(second_byte, base=16))


@pytest.mark.parametrize("arg", [0x123, 0x552, 0xF4A, 0x345, 0xBC3])
def test_return_from_subroutine(cpu, arg):
    cpu.return_from_subroutine(arg)
    assert cpu.PC == arg


@pytest.mark.parametrize("arg", [0x123, 0x552, 0xF4A, 0x345, 0xBC3])
def test_halt_machine(cpu, arg):
    cpu.halt_machine(arg)
    assert cpu.halted
    assert cpu.PC == arg


def test_get_data(cpu):
    pass

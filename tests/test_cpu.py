from pathlib import Path

import numpy as np
import pytest

from src.cpu import CPU
from src.memory import Byte, Memory, Word
from src.loader import Loader
from hypothesis import given
from hypothesis.strategies import integers


@pytest.fixture
def memory():
    mem = Memory()
    for i in range(4096):
        mem[i] = Byte(i % 256)

    path = Path().resolve().joinpath("data/test.bin")
    loader = Loader(mem)
    loader.load(path, 0)
    return mem


@pytest.fixture
def cpu(memory):
    cpu = CPU(memory)
    return cpu


def test_fetch(cpu, PC):
    cpu.PC = PC
    cpu.fetch()
    assert cpu.PC == PC +2
    assert cpu.instruction == Word(Byte(0), Byte(1))
    cpu.fetch()
    assert cpu.PC == 1028
    assert cpu.instruction == Word(Byte(2), Byte(3))
    cpu.fetch()
    assert cpu.PC == 1030
    assert cpu.instruction == Word(Byte(4), Byte(5))

    cpu.PC = 4092
    cpu.fetch()
    assert cpu.PC == 4094
    assert cpu.instruction == Word(Byte(252), Byte(253))
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
    assert cpu.decode() == (cpu.opcode[opcode], np.int16(arg))


@pytest.mark.parametrize("arg", [0x100, 0x300, 0x123, 0xFF3])
def test_jmp(cpu, arg):
    if arg % 2 != 0:
        with pytest.raises(ValueError):
            cpu.jmp(arg)
    else:
        cpu.jmp(arg)
        assert cpu.PC == arg


@pytest.mark.parametrize(
    "AC, arg, expected_output",
    [
        (0, 0x100, 0x100),
        (1, 0x300, 0),
        (-3, 0x123, 0),
        (-3, 0x124, 0),
        (0, 0xFF3, 0xFF3),
    ],
)
def test_jmp_if_zero(cpu, AC, arg, expected_output):
    cpu.AC = AC
    if arg % 2 != 0 and AC == 0:
        with pytest.raises(ValueError):
            cpu.jmp_if_zero(arg)
    else:
        cpu.jmp_if_zero(arg)
        assert cpu.PC == expected_output


@pytest.mark.parametrize(
    "AC, arg, expected_output",
    [
        (0, 0x100, 0),
        (1, 0x300, 0),
        (-3, 0x123, 'error'),
        (-3, 0x124, 0x124),
        (0x892, 0xFF3, 'error'),
        (0xFFF, 0xFFE, 0xFFE),
    ],
)
def test_jmp_if_negative(cpu, AC, arg, expected_output):
    cpu.AC = AC
    print("printing AC")
    print(cpu.AC)
    if arg % 2 != 0 and cpu.AC < 0:
        with pytest.raises(ValueError):
            cpu.jmp_if_negative(arg)
    else:
        cpu.jmp_if_negative(arg)
        assert cpu.PC == expected_output


@pytest.mark.parametrize(
    "arg, expected",
    [(123, 123), (0, 0), (0x801, -2047), (0xFFF, -1), (0x800, -2048), (0x7FF, 2047)],
)
def test_load_value(cpu, arg, expected):
    cpu.load_value(arg)
    assert cpu.AC == expected


@pytest.mark.parametrize("AC, arg", [(10, 336), (0x800, 265), (3, 0x550), (0, 0xFF0)])
def test_add(cpu, AC, arg):
    cpu.AC = AC
    cpu.add(arg)
    assert cpu.AC == CPU.sign_extend(AC + (arg % 256))
    assert type(cpu.AC) is np.int16


@pytest.mark.parametrize(
    "AC, arg", [(10, 0x334), (0xF10, 0x35), (3, 0x550), (0, 0xFF0)]
)
def test_subtract(cpu, AC, arg):
    cpu.AC = AC
    cpu.subtract(arg)
    assert cpu.AC == AC - (arg % 256)
    assert type(cpu.AC) is np.int16


@pytest.mark.parametrize(
    "AC, arg", [(10, 0x334), (-0x812, 0x35), (3, 0x550), (0, 0xFF0)]
)
def test_multiply(cpu, AC, arg):
    cpu.AC = AC
    cpu.multiply(arg)
    assert cpu.AC == AC * (arg % 256)
    assert type(cpu.AC) is np.int16


@pytest.mark.parametrize("AC, arg", [(10, 256), (-33, 0x35), (3, 0x550), (0, 0xFF0)])
def test_divide(cpu, AC, arg):
    cpu.AC = AC
    if (arg % 256) == 0:
        with pytest.raises(ZeroDivisionError):
            cpu.divide(arg)
    else:
        cpu.divide(arg)
        assert cpu.AC == int(AC / (arg % 256))
        assert type(cpu.AC) is np.int16


@pytest.mark.parametrize("arg", [0x552, 0xF4A, 0x345, 0xBB3])
def test_load_from_memory(cpu, arg):
    cpu.load_from_memory(arg)
    assert cpu.AC == cpu.memory[arg].value
    assert type(cpu.AC) is np.int16


@pytest.mark.parametrize("AC, arg", [(10, 0x334), (0, 0x35), (0xFA, 0x550), (0, 0xFF0), (0xFFF, 4032)])
def test_move_to_memory(cpu, AC, arg):
    cpu.AC = AC
    cpu.move_to_memory(arg)
    assert cpu.memory[arg] == Byte(AC)


@pytest.mark.parametrize(
    "PC, arg", [(0x124, 0x552), (0xF3A, 0xF4A), (0x00, 0x345), (0x9A, 0xBC3)]
)
def test_subroutine_call(cpu, PC, arg):
    cpu.PC = PC
    if arg % 2 != 0:
        with pytest.raises(ValueError):
            cpu.subroutine_call(arg)
    else:
        cpu.subroutine_call(arg)
        first_nibble = format(PC, "03x")[0]
        second_byte = format(PC, "03x")[1:]
        assert cpu.PC == arg + 2
        assert cpu.memory[arg] == Byte(int(first_nibble, base=16))
        assert cpu.memory[arg + 1] == Byte(int(second_byte, base=16))


@pytest.mark.parametrize(
    "arg, expected_result", [(257, 0x102), (271, 3856), (1801, 0x90A)]
)
def test_return_from_subroutine(cpu, arg, expected_result):
    cpu.return_from_subroutine(arg)
    assert cpu.PC == expected_result


@pytest.mark.parametrize("arg", [0x123, 0x552, 0xF4A, 0x345, 0xBC3])
def test_halt_machine(mocker, cpu, arg):
    mocker.patch("builtins.input", return_value="blabla")
    if arg % 2 != 0:
        with pytest.raises(ValueError):
            cpu.halt_machine(arg)
    else:
        cpu.halt_machine(arg)
        input.assert_called_once()
        assert cpu.PC == arg


@pytest.mark.parametrize(
    "user_inputs, expected_output", [("498", 498), ("/224", 0x224), ("/F00", 0xF00)]
)
def test_process_user_input(mocker, cpu, user_inputs, expected_output):
    mocker.patch("builtins.input", return_value=user_inputs)
    assert not cpu.process_user_input()
    assert cpu.PC == expected_output


@pytest.mark.parametrize(
    "user_inputs",
    ["11", "-10", "lol\n", "-A3", "i love pizza", "新しいウイルスの病気", "34343434", "AF00"],
)
def test_process_user_input_errors(mocker, cpu, user_inputs):
    mocker.patch("builtins.input", return_value=user_inputs)
    assert cpu.process_user_input()


@pytest.mark.parametrize("AC", [0, 1234, -55, -1])
def test_put_data(capsys, cpu, AC):
    cpu.AC = AC
    cpu.put_data()
    captured = capsys.readouterr()
    assert captured.out == str(AC) + "\n"

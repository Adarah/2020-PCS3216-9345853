import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import builds, integers

from src.cpu import CPU
from src.memory import Byte, Memory, Word
from loguru import logger

pytestmark = [pytest.mark.hypothesis]


def bytes_strat(min, max):
    return builds(Byte, integers(min, max))


def ac_strat(min, max):
    return integers(min_value=min, max_value=max).map(lambda x: CPU.sign_extend(x))


even_positions = integers(min_value=0, max_value=2047).map(lambda x: 2 * x)
bytes = bytes_strat(0, 255)
arg = integers(min_value=0, max_value=4095)
ac = ac_strat(0, 0xFFF)


@pytest.fixture(scope="module")
def cpu():
    return CPU(Memory())


@given(msb=bytes, lsb=bytes, PC=even_positions)
def test_fetch(cpu, msb, lsb, PC):
    cpu.memory[PC] = msb
    cpu.memory[PC + 1] = lsb
    cpu.PC = PC
    cpu.fetch()
    assert cpu.PC == PC + 2
    assert cpu.instruction == Word(cpu.memory[PC], cpu.memory[PC + 1])


@given(msb=bytes, lsb=bytes)
def test_decode(cpu, msb, lsb):
    cpu.instruction = Word(msb, lsb)
    expected_arg = msb.second_nibble * 0x100 + lsb.value
    assert cpu.decode() == (cpu.opcode[msb.first_nibble], expected_arg)


@given(arg=arg)
def test_jmp(cpu, arg):
    if arg % 2 == 0:
        cpu.jmp(arg)
        assert cpu.PC == arg
    else:
        with pytest.raises(ValueError):
            cpu.jmp(arg)


@given(arg=even_positions, ac=ac)
def test_jmp_if_zero(cpu, arg, ac):
    starting_pc = cpu.PC
    cpu.AC = ac
    cpu.jmp_if_zero(arg)
    if ac == 0:
        assert cpu.PC == arg
    else:
        assert cpu.PC == starting_pc


@given(arg=even_positions, ac=ac)
def test_jmp_if_negative(cpu, arg, ac):
    starting_pc = cpu.PC
    cpu.AC = ac
    cpu.jmp_if_negative(arg)
    if ac < 0:
        assert cpu.PC == arg
    else:
        assert cpu.PC == starting_pc


@given(arg=arg)
def test_load_value(cpu, arg):
    cpu.load_value(arg)
    assert cpu.AC == CPU.sign_extend(arg)


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=3000)
@pytest.mark.math
def test_add(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    print(msb)
    print(ac)
    cpu.add(arg)
    print(cpu.AC)
    assert cpu.AC == CPU.sign_extend(ac + CPU.sign_extend(cpu.memory[arg].value))


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=3000)
@pytest.mark.math
def test_subtract(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.subtract(arg)
    assert cpu.AC == CPU.sign_extend(ac - CPU.sign_extend(cpu.memory[arg].value))


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=3000)
@pytest.mark.math
def test_multiply(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.multiply(arg)
    assert cpu.AC == CPU.sign_extend(ac * CPU.sign_extend(cpu.memory[arg].value))


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=3000)
@pytest.mark.math
def test_divide(cpu, arg, ac, msb):
    assume(msb.value != 0)
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.divide(arg)
    assert cpu.AC == CPU.sign_extend(ac // CPU.sign_extend(cpu.memory[arg].value))


@given(arg=arg, msb=bytes)
def test_load_from_memory(cpu, arg, msb):
    cpu.memory[arg] = msb
    cpu.load_from_memory(arg)
    assert cpu.AC == msb.value


@given(arg=arg, ac=ac)
def test_move_to_memory(cpu, arg, ac):
    cpu.AC = ac
    hex_value = format(ac, '04X')
    msb = hex_value[:2]
    lsb = hex_value[2:]
    cpu.move_to_memory(arg)
    print(hex_value)
    assert cpu.memory[arg] == Byte.from_hex(msb)
    assert cpu.memory[arg + 1] == Byte.from_hex(lsb)

import pytest
from hypothesis import assume, given, settings
from hypothesis.strategies import builds, integers, text
from loguru import logger

from src.cpu import CPU
from src.memory import Byte, Memory, Word

pytestmark = [pytest.mark.hypothesis]


def bytes_strat(min, max):
    return builds(Byte, integers(min, max))


even_positions = integers(min_value=0, max_value=2047).map(lambda x: 2 * x)
bytes = bytes_strat(0, 255)
arg = integers(min_value=0, max_value=4095)
ac = bytes


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
    cpu.jmp(arg)
    assert cpu.PC == arg


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
    assert cpu.AC == Byte(arg)


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_add(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.add(arg)
    assert cpu.AC == (ac + cpu.memory[arg])


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_subtract(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.subtract(arg)
    assert cpu.AC == ac - cpu.memory[arg].value


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_add_sub(cpu, arg, ac, msb):
    logger.debug(f"AC started at: {ac}")
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.add(arg)
    cpu.subtract(arg)
    assert cpu.AC == ac


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_sub_add(cpu, arg, ac, msb):
    logger.debug(f"AC started at: {ac}")
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.subtract(arg)
    cpu.add(arg)
    assert cpu.AC == ac


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_multiply(cpu, arg, ac, msb):
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.multiply(arg)
    assert cpu.AC == ac * cpu.memory[arg].value


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_divide(cpu, arg, ac, msb):
    assume(msb.value != 0)
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.divide(arg)
    assert cpu.AC == ac // cpu.memory[arg].value


# Could not find a good testing condition in case overflow happens.
# @given(arg=arg, ac=ac, msb=bytes)
# @settings(max_examples=1000)
# @pytest.mark.math
# def test_mul_div(cpu, arg, ac, msb):
#     logger.debug("-"*10 + f"AC started at {ac}")
#     assume(msb != 0)
#     cpu.memory[arg] = msb
#     cpu.AC = ac
#     cpu.multiply(arg)
#     cpu.divide(arg)
#     assert abs(cpu.AC - ac) < abs(cpu.memory[arg])


@given(arg=arg, ac=ac, msb=bytes)
@settings(max_examples=1000)
@pytest.mark.math
def test_div_mul(cpu, arg, ac, msb):
    assume(msb != 0)
    cpu.memory[arg] = msb
    cpu.AC = ac
    cpu.divide(arg)
    cpu.multiply(arg)
    assert abs(cpu.AC - ac) < abs(cpu.memory[arg])


@given(arg=arg, byte=bytes)
def test_load_from_memory(cpu, arg, byte):
    cpu.memory[arg] = byte
    cpu.load_from_memory(arg)
    assert cpu.AC == byte


@given(arg=arg, ac=ac)
def test_move_to_memory(cpu, arg, ac):
    cpu.AC = ac
    cpu.move_to_memory(arg)
    assert cpu.memory[arg] == ac


@given(arg=even_positions, PC=even_positions)
def test_subroutine_call(cpu, arg, PC):
    cpu.PC = PC
    first_byte = int(format(PC, "04X")[:2], 16)
    second_byte = int(format(PC, "04X")[2:], 16)
    cpu.subroutine_call(arg)
    assert cpu.memory[arg] == Byte(first_byte)
    assert cpu.memory[arg + 1] == Byte(second_byte)
    assert cpu.PC == arg + 2


@given(
    arg=even_positions,
    PC=even_positions,
    msb=bytes_strat(0, 0xF),
    lsb=bytes_strat(0, 127).map(lambda x: x * 2),
)
def test_return_from_subroutine(cpu, arg, PC, msb, lsb):
    cpu.memory[arg] = msb
    cpu.memory[arg + 1] = lsb
    new_PC = (
        cpu.memory[arg].second_nibble * 0x100
        + cpu.memory[arg + 1].first_nibble * 0x10
        + cpu.memory[arg + 1].second_nibble
    )
    cpu.return_from_subroutine(arg)
    assert cpu.PC == new_PC


@given(arg=even_positions, user_input=text())
def test_halt_machine(cpu, arg, module_mocker, user_input):
    module_mocker.patch("builtins.input", return_value=user_input)
    cpu.halt_machine(arg)
    input.assert_called_once()
    assert cpu.PC == arg


def test_get_data(cpu):
    pass

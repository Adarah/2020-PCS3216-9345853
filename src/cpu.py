from typing import Callable, Dict

import attr
from loguru import logger

import sys
import importlib.resources
from src import data

try:
    from memory import Byte, Memory, Word
except ImportError:
    from .memory import Byte, Memory, Word


@attr.s
class CPU:

    memory: Memory = attr.ib(repr=False)
    trace: bool = attr.ib(default=False)
    _PC: int = attr.ib(
        default=0, validator=attr.validators.instance_of(int), init=False
    )
    instruction: Word = attr.ib(default=None, init=False)
    _AC: Byte = attr.ib(
        default=Byte(0), validator=attr.validators.instance_of(Byte), init=False
    )
    opcode: Dict[int, Callable] = attr.ib(default=None, init=False, repr=False)
    read_offset: int = attr.ib(default=0, init=False, repr=False)

    def __attrs_post_init__(self):
        self.opcode = {
            0x0: self.jmp,
            0x1: self.jmp_if_zero,
            0x2: self.jmp_if_negative,
            0x3: self.load_value,
            0x4: self.add,
            0x5: self.subtract,
            0x6: self.multiply,
            0x7: self.divide,
            0x8: self.load_from_memory,
            0x9: self.move_to_memory,
            0xA: self.subroutine_call,
            0xB: self.return_from_subroutine,
            0xC: self.halt_machine,
            0xD: self.get_data,
            0xE: self.put_data,
            0xF: self.os_call,
        }

    @property
    def AC(self):
        return self._AC

    @AC.setter
    def AC(self, value):
        if type(value) is not Byte:
            self._AC = Byte(value)
        else:
            self._AC = value

    @property
    def PC(self):
        return self._PC

    @PC.setter
    def PC(self, value):
        if (value < 0) or (value > 4096):
            raise IndexError

        self._PC = value

    def fetch(self):
        if self.trace:
            print(f"PC: {self.PC}")
            print(f"AC: {self.AC}")
            print("Trace Mode ON")
            command = input("Input TR to turn it off, or anything else to proceed: ")
            if command.strip() == "TR":
                self.trace = False
        self.instruction = Word(*self.memory[self.PC : self.PC + 2])
        logger.debug(f"Fetching next instruction: {self.instruction}")
        self.PC += 2

    def decode(self):
        function = self.opcode[self.instruction.first_byte.first_nibble]
        arg = (
            self.instruction.first_byte.second_nibble * 0x100
            + self.instruction.second_byte.value
        )
        logger.debug(f"Decoding instruction: {self.instruction}")
        logger.debug(f"Operation: {function.__name__}")
        logger.debug(f"Argument: {arg} == /{arg:03X}")
        return function, arg

    def jmp(self, arg):
        logger.debug(f"Setting PC to {arg}")
        self.PC = arg

    def jmp_if_zero(self, arg):
        logger.debug("Conditional jump if AC is zero")
        logger.debug(f"AC: {self.AC}")
        if self.AC == 0:
            logger.debug(f"Setting PC to {arg}")
            self.PC = arg

    def jmp_if_negative(self, arg):
        logger.debug("Conditional jump if AC is less than zero")
        logger.debug(f"AC: {self.AC}")
        if self.AC < 0:
            logger.debug(f"Setting PC to {arg}")
            self.PC = arg

    def load_value(self, arg):
        logger.debug(f"Loading {arg} into AC")
        self.AC = arg

    def add(self, arg):
        self.AC += self.memory[arg]
        logger.debug(f"Adding /{self.memory[arg]:03X} to AC")
        logger.debug(f"AC is now {self.AC}")

    def subtract(self, arg):
        self.AC -= self.memory[arg]
        logger.debug(
            f"Subtracting value in memory position {arg} == /{self.memory[arg]:03X} from AC"
        )
        logger.debug(f"AC is now {self.AC}")

    def multiply(self, arg):
        self.AC *= self.memory[arg]
        logger.debug(
            f"Multiplying AC by the value in memory position {arg} == /{self.memory[arg]:03X}"
        )
        logger.debug(f"AC is now {self.AC}")

    def divide(self, arg):
        if self.memory[arg] == 0:
            raise ZeroDivisionError

        self.AC //= self.memory[arg]
        logger.debug(
            f"Dividing AC by the value in memory position {arg} == /{self.memory[arg]:03X}"
        )
        logger.debug(f"AC is now {self.AC}")

    def load_from_memory(self, arg):
        logger.debug(f"Settings AC to {self.memory[arg]}")
        self.AC = self.memory[arg]

    def move_to_memory(self, arg):
        logger.debug(f"Moving AC == {self.AC:04X} to memory position {arg}")
        self.memory[arg] = self.AC

    def subroutine_call(self, arg):
        self.memory[arg] = Byte((self.PC & 0xF00) >> 8)
        self.memory[arg + 1] = Byte(self.PC & 0x0FF)
        self.PC = arg + 2
        logger.debug(f"Storing current PC in memory positions {arg} and {arg+1}")
        logger.debug(f"Current PC is now {self.PC}")

    def return_from_subroutine(self, arg):
        first_byte = format(self.memory[arg], "x")
        second_byte = format(self.memory[arg + 1], "x")
        if self.memory[arg] > 0xF:
            logger.critical(
                f"""The element in memory position {arg} is larger than 0xF, so
                PC will overflow. {self.memory[arg]} should have been a value between 0
                and F"""
            )
            raise OverflowError
        self.PC = int(first_byte + second_byte, 16)

        logger.debug(f"Returning from subroutine. PC is now {self.PC}")

    def halt_machine(self, arg):
        logger.debug("Halting all operations.")
        input("System halted. Press Enter to resume operations.")
        self.PC = arg

    def get_data(self, _=None):
        with importlib.resources.path(data, "program.bin") as path, open(
            path, "rb"
        ) as f:
            f.seek(self.memory.read_offset)
            file_data = int.from_bytes(f.read(1), "big")
            self.AC = Byte(file_data)
        self.memory.read_offset += 1
        logger.debug(f"setting AC to {self.AC}")
        logger.debug(f"read_offset: {self.memory.read_offset}")

    def put_data(self, _=None):
        logger.debug(f"writing {self.AC} to the output file")
        with importlib.resources.path(data, "output.txt") as path, open(path, "a") as f:
            f.write(str(self.AC.unsigned))
            f.write("\n")

    def os_call(self, arg):
        if arg == 0:
            sys.exit(0)
        raise NotImplementedError


if __name__ == "__main__":
    mem = Memory()
    cpu = CPU(mem, trace=False)
    while True:
        cpu.fetch()
        foo, arg = cpu.decode()
        foo(arg)

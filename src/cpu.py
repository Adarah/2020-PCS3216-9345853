import attr
import numpy as np
from loguru import logger

from .memory import Byte, Memory, Word


@attr.s
class CPU:

    memory: Memory = attr.ib()
    PC: int = attr.ib(default=0)
    instruction: Word = attr.ib(default=None)
    _AC: np.int16 = attr.ib(
        default=np.int16(0), validator=attr.validators.instance_of(np.int16)
    )
    halted: bool = attr.ib(default=False)
    trace: bool = attr.ib(default=False)
    opcode: dict = attr.ib(default=None)

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
        self._AC = np.int16(value)

    def fetch(self):
        if self.PC + 2 > 4096:
            logger.error("Program Counter(+2) is pointing a value larger than 4096")
            raise IndexError
        self.instruction = Word(*self.memory[self.PC : self.PC + 2])
        logger.debug(f"Fetching next instruction: {self.instruction}")
        self.PC += 2

    def decode(self):
        function = self.opcode[self.instruction.first_byte.first_nibble]
        arg = (
            self.instruction.first_byte.second_nibble * 16 ** 2
            + self.instruction.second_byte.value
        )
        logger.debug(f"Decoding instruction: {self.instruction}")
        logger.debug(f"Operation: {function}")
        logger.debug(f"Argument: {arg}")
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
        self.AC += self.memory[arg].value
        logger.debug(f"Adding {arg} to AC")
        logger.debug(f"AC is now {self.AC}")

    def subtract(self, arg):
        self.AC -= self.memory[arg].value
        logger.debug(f"Subtracting {arg} from AC")
        logger.debug(f"AC is now {self.AC}")

    def multiply(self, arg):
        self.AC *= self.memory[arg].value
        logger.debug(f"Multiplying AC by {arg}")
        logger.debug(f"AC is now {self.AC}")

    def divide(self, arg):
        if self.memory[arg].value == 0:
            raise ZeroDivisionError

        self.AC /= self.memory[arg].value
        logger.debug(f"Dividing AC by {arg}")
        logger.debug(f"AC is now {self.AC}")

    def load_from_memory(self, arg):
        self.AC = self.memory[arg].value
        logger.debug(f"Setting AC to the value found in memory position {arg}")
        logger.debug(f"AC is now {self.AC}")

    def move_to_memory(self, arg):
        self.memory[arg] = Byte(self.AC)
        logger.debug(f"Moving AC to memory position {arg}")
        logger.debug(f"Address {arg} now stores {self.AC}")

    def subroutine_call(self, arg):
        self.memory[arg] = Byte((self.PC & 0xF00) >> 8)
        self.memory[arg + 1] = Byte(self.PC & 0x0FF)
        self.PC = arg + 2
        logger.debug(f"Storing current PC in memory positions {arg} and {arg+1}")
        logger.debug(f"Current PC is now {self.PC}")

    def return_from_subroutine(self, arg):
        self.PC = arg
        logger.debug(f"Returning from subroutine. PC is now {self.PC}")

    def halt_machine(self, arg):
        logger.debug("Halting all operations.")
        self.halted = True
        self.PC = arg

    def get_data(self):
        pass

    def put_data(self):
        pass

    def os_call(self):
        raise NotImplementedError


if __name__ == "__main__":
    mem = Memory()
    cpu = CPU(mem)
    cpu.load_value(0x123)
    cpu.fetch()
    cpu.load_value(0x445)

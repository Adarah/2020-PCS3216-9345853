from typing import Callable, Dict

import attr
import numpy as np
from loguru import logger

from .memory import Byte, Memory, Word


@attr.s
class CPU:

    memory: Memory = attr.ib()
    trace: bool = attr.ib(default=False)
    _PC: int = attr.ib(
        default=0, validator=attr.validators.instance_of(int), init=False
    )
    instruction: Word = attr.ib(default=None, init=False)
    _AC: np.int16 = attr.ib(
        default=np.int16(0), validator=attr.validators.instance_of(np.int16), init=False
    )
    opcode: Dict[int, Callable] = attr.ib(default=None, init=False)

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
        self._AC = CPU.sign_extend(value)

    @property
    def PC(self):
        return self._PC

    @PC.setter
    def PC(self, value):
        if (value < 0) or (value > 4096):
            raise IndexError
        if (value % 2 != 0):
            raise ValueError

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
        self.AC += CPU.sign_extend(self.memory[arg].value)
        logger.debug(
            f"Adding value in memory position {arg} == /{self.memory[arg].value:03X} to AC"
        )
        logger.debug(f"AC is now {self.AC}")

    def subtract(self, arg):
        self.AC -= CPU.sign_extend(self.memory[arg].value)
        logger.debug(
            f"Subtracting value in memory position {arg} == /{self.memory[arg].value:03X} from AC"
        )
        logger.debug(f"AC is now {self.AC}")

    def multiply(self, arg):
        self.AC *= CPU.sign_extend(self.memory[arg].value)
        logger.debug(
            f"Multiplying AC by the value in memory position {arg} == /{self.memory[arg].value:03X}"
        )
        logger.debug(f"AC is now {self.AC}")

    def divide(self, arg):
        if self.memory[arg].value == 0:
            raise ZeroDivisionError

        self.AC //= CPU.sign_extend(self.memory[arg].value)
        logger.debug(
            f"Dividing AC by the value in memory position {arg} == /{self.memory[arg].value:03X}"
        )
        logger.debug(f"AC is now {self.AC}")

    def load_from_memory(self, arg):
        self.AC = self.memory[arg].value
        logger.debug(f"Setting AC to the value found in memory position {arg}")
        logger.debug(f"AC is now {self.AC}")

    def move_to_memory(self, arg):
        logger.debug(f"Moving {self.AC:04X} MSB to memory position {arg}")
        logger.debug(f"Moving {self.AC:04X} LSB to memory position {arg + 1}")
        ac_hex = int(self.AC).to_bytes(2, 'big', signed=True)
        msb = ac_hex[0]
        lsb = ac_hex[1]
        print(format(self.AC, '04X'))
        self.memory[arg] = msb
        self.memory[arg + 1] = lsb

    def subroutine_call(self, arg):
        self.memory[arg] = Byte((self.PC & 0xF00) >> 8)
        self.memory[arg + 1] = Byte(self.PC & 0x0FF)
        self.PC = arg + 2
        logger.debug(f"Storing current PC in memory positions {arg} and {arg+1}")
        logger.debug(f"Current PC is now {self.PC}")

    def return_from_subroutine(self, arg):
        first_byte = self.memory[arg].value
        second_byte = self.memory[arg + 1].value
        if first_byte > 0xF:
            logger.critical(
                f"""The element in memory position {arg} is larger than 0xF, so
                PC will overflow. {self.memory[arg]} should have been a value between 0
                and F"""
            )
            raise OverflowError
        self.PC = first_byte * 0x100 + second_byte

        logger.debug(f"Returning from subroutine. PC is now {self.PC}")

    def halt_machine(self, arg):
        logger.debug("Halting all operations.")
        input("System halted. Press Enter to resume operations.")
        self.PC = arg

    def get_data(self, _=None):
        logger.debug("Collecting user inputs")
        while self.process_user_input():
            continue

    def process_user_input(self):
        """Had to create this function for testing purposes. Tests were in an
        infinite loop after mocking the user input to something invalid"""
        user_input = input("Input the value to be set in the PC").strip()
        try:
            if user_input[0] == "/":  # numbers with a leading / are treated as hex
                value = int(user_input[1:], 16)
            else:
                value = int(user_input)

            self.PC = value

        except (ValueError, OverflowError):
            logger.debug(f"Invalid input attempted: {user_input}")
            print("Invalid input. Expected value in the range [0, 4096[")
            return 1

        return 0

    def put_data(self, _=None):
        """Poorly named instruction. It "puts" the data in stdout, i.e. prints it """
        print(self.AC)

    def os_call(self):
        raise NotImplementedError

    @staticmethod
    def sign_extend(val: int) -> np.int16:
        msb = (val & 1 << 11) >> 11
        if msb == 1:
            val |= 0xF000
        return np.int16(val)


if __name__ == "__main__":
    mem = Memory()
    cpu = CPU(mem, False)
    cpu.load_value(0x123)
    cpu.fetch()
    cpu.load_value(0x445)
    cpu.fetch()
    cpu.put_data(123)

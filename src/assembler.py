import argparse
import importlib.resources
from pathlib import Path
from typing import Dict, List

import attr
import pyparsing as pp
from loguru import logger
from pyparsing import *

from memory import Byte
from src import data


@attr.s
class Assembler:

    input_file: Path = attr.ib()
    file_start: int = attr.ib(init=False, default=0)
    file_end: int = attr.ib(init=False, default=0)
    file_len: int = attr.ib(init=False, default=0)
    symbols_table: Dict = attr.ib(init=False, default={})
    tokens: List = attr.ib(repr=False, init=False, default=[])

    def __attrs_post_init__(self):
        self.keywords = Assembler.make_keywords_parser()

        self.hex_args = Literal("/").suppress() + Word(hexnums)
        self.hex_args.setParseAction(lambda x: Assembler.check_big_int(int(x[0], 16)))

        self.int_args = Word(nums)
        self.int_args.setParseAction(lambda x: Assembler.check_big_int(int(x[0])))
        self.comment = Group(Literal(";").suppress()[1, ...] + Word(printables)[1, ...])

    @staticmethod
    def check_big_int(number):
        if number >= 4096:
            logger.critical(f"{number} cannot be represented in 12 bits")
            raise ValueError
        return format(number, "03X")

    @staticmethod
    def make_keyword(full_name, shorthand=None, opcode=0):
        parser = Keyword(full_name, caseless=True)
        if shorthand is not None:
            parser |= Keyword(shorthand, caseless=True)
        return parser.setParseAction(lambda token: f"{opcode:X}")

    @staticmethod
    def make_keywords_parser():
        keywords = (
            JP := Assembler.make_keyword("JP", "J", 0)
            | (JZ := Assembler.make_keyword("JZ", "Z", 1))
            | (JN := Assembler.make_keyword("JN", "N", 2))
            | (LV := Assembler.make_keyword("LV", "V", 3))
            | (add := Assembler.make_keyword("+", None, 4))
            | (subtract := Assembler.make_keyword("-", None, 5))
            | (multiply := Assembler.make_keyword("*", None, 6))
            | (divide := Assembler.make_keyword("/", None, 7))
            | (LD := Assembler.make_keyword("LD", "L", 8))
            | (MM := Assembler.make_keyword("MM", "M", 9))
            | (SC := Assembler.make_keyword("SC", "S", 10))
            | (RS := Assembler.make_keyword("RS", "R", 11))
            | (HM := Assembler.make_keyword("HM", "H", 12))
            | (GD := Assembler.make_keyword("GD", "G", 13))
            | (PD := Assembler.make_keyword("PD", "P", 14))
            | (OS := Assembler.make_keyword("OS", "O", 15))
        )
        return keywords

    def assign_start(self, token):
        self.file_start = int(token[1], 16)

    def assign_end(self, token):
        self.file_end = self.file_start + self.file_len
        return ["0", f"{self.file_start:03X}"]

    def make_pseudo_parser(self):
        args = self.hex_args | self.int_args
        start = Keyword("@") + args
        start.setParseAction(self.assign_start)

        constant = Word(alphas, alphanums + "_") + Keyword("K") + args
        constant.setParseAction(self.add_constant)

        end = Keyword("#") + Optional(Word(alphas, alphanums + "_"))
        end.setParseAction(self.assign_end)

        pseudo = start.suppress() | constant | end
        return pseudo

    def add_constant(self, token):
        var_name = token[0]
        if var_name in self.symbols_table:
            raise ValueError(
                f"Symbol {var_name} already previously declared, naming conflict occurred"
            )
        self.symbols_table[var_name] = self.file_start + self.file_len
        self.file_len += 1

    def add_to_symbols_table(self, token):
        if token in self.symbols_table:
            raise ValueError(
                f"Symbol {var_name} already previously declared, naming conflict occurred"
            )
        self.symbols_table[token] = self.file_start + self.file_len

    def add_to_file_len(self):
        self.file_len += 2

    def step_one(self):
        directive = Word(alphas, alphanums + "_").setParseAction(
            lambda x: self.add_to_symbols_table(x[0])
        )
        statement = self.keywords + (
            self.hex_args | self.int_args | Word(alphanums + "_")
        )
        statement.setParseAction(self.add_to_file_len)

        pseudo = self.make_pseudo_parser()
        step_one_parser = self.comment.suppress() | (
            directive ^ statement ^ pseudo
        ) + Optional(self.comment.suppress())

        with open(self.input_file, "r") as f:
            while (line := f.readline()) :
                line = line.strip()
                if not line:
                    continue
                res = list(step_one_parser.parseString(line))
                if self.file_end >= 4096:
                    raise IndexError(
                        f"""The program will not fit in memory
                    Initial address: {self.file_start}
                    Program length: {self.file_len}
                    {self.file_start + self.file_len} >= 4096"""
                    )
                self.tokens.append(res)

    def step_two(self):
        # print(self.tokens)
        partial_result = []  # opcodes with symbols substituted by their addresses
        for token in self.tokens:
            if type(token) == list and len(token) == 2:
                try:
                    int(token[1], 16)
                    token = "".join(token)
                except ValueError:
                    if token[1] not in self.symbols_table:
                        raise ValueError("Symbol was never previosly declared")
                    token[1] = format(self.symbols_table[token[1]], "03X")
                    token = "".join(token)
            if type(token) == list and len(token) == 3:
                token = token[2][1:]
            if type(token) != list:
                partial_result.append(token)
        partial_result = [
            "0" + format(self.file_start, "03X"),
            format(self.file_len, "X"),
        ] + partial_result
        # print(partial_result)

        result = []
        for word in partial_result:
            if len(word) > 2:
                msb = int(word[:2], 16)
                lsb = int(word[2:], 16)
                result.append(msb)
                result.append(lsb)
            else:
                result.append(int(word, 16))
        checksum = Byte(sum(result[:-2])).unsigned
        result.insert(3, checksum)
        result = bytearray(result)

        # path = Path(__file__).resolve().parent.joinpath("data/program.bin")
        with importlib.resources.path(data, "program.bin") as path, open(
            path, "wb"
        ) as f:
            f.write(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    with importlib.resources.path(data, "fibonacci.asm") as path:
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="path to the file to be assembled",
            required=False,
            default=path,
        )
    args = parser.parse_args()

    ass = Assembler(args.file)
    ass.step_one()
    ass.step_two()

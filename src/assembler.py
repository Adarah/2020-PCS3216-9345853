import attr
import pyparsing as pp
from typing import Dict
from pyparsing import *
from loguru import logger


@attr.s
class Assembler:

    path_to_file: str = attr.ib()
    save_location: str = attr.ib(default="./build/")
    # mnemonics: Dict[str, int] = attr.ib(init=False)
    # mnemonic_to_opcode: Dict[str, str] = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.keywords = set("JJ", "J", "JZ", "Z")
        self.mnemonic_to_opcode = {
            "JP": "0",
            "J": "0",
            "JZ": "1",
            "Z": "1",
            "JN": "2",
            "N": "2",
            "LV": "3",
            "V": "3",
            "+": "4",
            "-": "5",
            "*": "6",
            "/": "7",
            "LD": "8",
            "L": "8",
            "MM": "9",
            "M": "9",
            "SC": "A",
            "S": "A",
            "RS": "B",
            "R": "B",
            "HM": "C",
            "H": "C",
            "GD": "D",
            "G": "D",
            "PD": "E",
            "P": "E",
            "OS": "F",
            "O": "F",
        }


def make_parser():
    def make_keyword(full_name, shorthand=None, opcode=0):
        parser = Keyword(full_name, caseless=True)
        if shorthand is not None:
            parser |= Keyword(shorthand, caseless=True)
        return parser.setParseAction(lambda token: f"{opcode:X}")

    def check_big_hex(token):
        token = format(int(token[0], 16), "03X")
        if len(token) > 3:
            logger.critical(f"{token} cannot be represented in 12 bits")
            raise ValueError
        return token

    def check_big_int(token):
        token = int(token[0])
        if token >= 4096:
            logger.critical(f"{token} cannot be represented in 12 bits")
            raise ValueError
        return format(token, "03X")

    hex_args = Literal("/").suppress() + Word(hexnums)
    hex_args.setParseAction(check_big_hex)

    int_args = Word(nums)
    int_args.setParseAction(check_big_int)
    comment = Group(Literal(";").suppress()[1, ...] + Word(printables)[1, ...])

    statement = (
        JP := make_keyword("JP", "J", 0)
        | (JZ := make_keyword("JZ", "Z", 1))
        | (JN := make_keyword("JN", "N", 2))
        | (LV := make_keyword("LV", "V", 3))
        | (add := make_keyword("+", None, 4))
        | (subtract := make_keyword("-", None, 5))
        | (multiply := make_keyword("*", None, 6))
        | (divide := make_keyword("/", None, 7))
        | (LD := make_keyword("LD", "L", 8))
        | (MM := make_keyword("MM", "M", 9))
        | (SC := make_keyword("SC", "S", 10))
        | (RS := make_keyword("RS", "R", 11))
        | (HM := make_keyword("HM", "H", 12))
        | (GD := make_keyword("GD", "G", 13))
        | (PD := make_keyword("PD", "P", 14))
        | (OS := make_keyword("OS", "O", 15))
    ) + (hex_args | int_args)
    parser = comment.suppress() | (statement + Optional(comment.suppress()))
    return parser.setParseAction("".join)


"""
parsing input: wanted output
JMP 123 : 0123
J 123 : 0123
+ 23 : 4023
+ /23: 4045"""
test = """
JMP /123\n
JN 333\n
JN /23F\n
+ /33A\n
"""

jmp = pp.Keyword("JMP")

a = make_parser()
from pathlib import Path

with open(Path().resolve().joinpath("data/assembly.txt"), "r") as f:
    while (line := f.readline()) :
        if not line.strip():
            continue
        print(repr(line.strip()))
        print(a.parseString(line.strip()))

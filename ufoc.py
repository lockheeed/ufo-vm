from ctypes import c_uint8, c_uint16, c_uint32, c_uint64

import sys
import re
import struct
import string
import math
import codecs


#  OP  T   S
# 0000 00 00 exit
# 0001 00 00 mov
# 0010 00 00 add
# 0011 00 00 sub
# 0100 00 00 mul
# 0101 00 00 div
# 0110 00 00 xor
# 0111 00 00 and
# 1000 00 00 or
# 1001 00 00 rand
# 1010 00 00 ror
# 1011 00 00 rol
# 1100 00 00 lea
# 1101 00 00 jmp
# 1110 00 00 put
# 1111 00 00 get


USAGE_BANNER = 'Usage: ufoc.py <input.ufo> <output.bin> [verb (0, 1, 2)]'

ADDR_SIZE = 2


class SEGMENT:
    NONE = -1
    CODE = 0
    DATA = 1
    HEADER = 2

    name2id = {
        '.code': CODE,
        '.data': DATA,
    }


class DATA_TYPE:
    NONE = -1
    INT = 0
    ADDR = 1
    PTR = 2
    STR = 3
    FILE = 4


class Data:
    offset = 0
    size = 0
    data = b''

    def __init__(self, offset: int, size: int, data: bytes):
        self.offset = offset
        self.size = size
        self.data = data


REGISTER_LABLES = {
    'rip': 0,
    'r0': 8,
    'r1': 16,
    'r2': 24,
    'r3': 32,
    'r4': 40,
    'r5': 48,
    'r6': 56,
    'r7': 64,
    'r8': 72,
    'r9': 80
}


REGISTER_MEMORY_MAP = [
    Data(0*8, 8, bytes(8)),
    Data(1*8, 8, bytes(8)),
    Data(2*8, 8, bytes(8)),
    Data(3*8, 8, bytes(8)),
    Data(4*8, 8, bytes(8)),
    Data(5*8, 8, bytes(8)),
    Data(6*8, 8, bytes(8)),
    Data(7*8, 8, bytes(8)),
    Data(8*8, 8, bytes(8)),
    Data(9*8, 8, bytes(8)),
    Data(10*8, 8, bytes(8))
]


def pack_int(val: int, size: int) -> bytes:
    if size == 1:
        return struct.pack('<B', c_uint8(val).value)
    elif size == 2:
        return struct.pack('<H', c_uint16(val).value)
    elif size == 4:
        return struct.pack('<I', c_uint32(val).value)
    elif size == 8:
        return struct.pack('<Q', c_uint64(val).value)


class Allocator(object):
    def __init__(self) -> None:
        self.lables = REGISTER_LABLES.copy()
        self.memory_map = REGISTER_MEMORY_MAP.copy()

    def alloc(self, instr: str):
        size_modifiers = {
            'db': 1, 'dw': 2, 'dd': 4, 'dq': 8
        }

        name = None
        size = 0
        data = None
        data_type = DATA_TYPE.INT

        tokens = instr.split()

        if tokens[0] not in size_modifiers.keys():
            name = tokens[0]
            size = size_modifiers.get(tokens[1])
            tokens = tokens[2:]

        else:
            size = size_modifiers.get(tokens[0])
            tokens = tokens[1:]

        if tokens:
            if tokens[0][0] == '"':
                data_type = DATA_TYPE.STR
                data = ' '.join(tokens)

                if data[-1][-1] != '"':
                    raise Exception('Invalid string literal!')

                data = codecs.decode(data[1:-1], 'unicode_escape').encode()
                data += b'\x00'
                size = len(data)

            elif tokens[0].startswith('file'):
                data_type = DATA_TYPE.FILE

                if size != 1:
                    raise Exception('Invalid size modifier! Only "db" allowed with files.')

                filename = re.findall('file\((.*)\)', tokens[0])[0]
                data = open(filename, 'rb').read() + b'\x00'
                size = len(data)

            elif tokens[0][0] in string.digits + '-':
                if tokens[0].startswith('0x'):
                    val = int(tokens[0], 16)
                else:
                    val = int(tokens[0])

                data = pack_int(val, size)

            else:
                data = bytes(size)

        else:
            data = bytes(size)

        offset = 0
        if self.memory_map:
            offset += self.memory_map[-1].offset + self.memory_map[-1].size

        if data_type == DATA_TYPE.INT and offset % size != 0:
            offset -= offset % size - size

        data = Data(offset, size, data)
        self.memory_map.append(data)

        if name:
            if self.lables.get(name) is not None:
                raise Exception(f'Lable {name} already used!')

            self.lables[name] = offset

    def get_raw_memory_map(self) -> bytes:
        raw = b''
        for alloc in self.memory_map:
            raw = raw.ljust(alloc.offset, b'\x00')
            raw += alloc.data
        return raw


class Assembler(object):
    it_acaaap = (
        (DATA_TYPE.ADDR, DATA_TYPE.INT),
        (DATA_TYPE.ADDR, DATA_TYPE.ADDR),
        (DATA_TYPE.ADDR, DATA_TYPE.PTR)
    )

    it_acaaappa = (
        (DATA_TYPE.ADDR, DATA_TYPE.INT),
        (DATA_TYPE.ADDR, DATA_TYPE.ADDR),
        (DATA_TYPE.ADDR, DATA_TYPE.PTR),
        (DATA_TYPE.PTR, DATA_TYPE.ADDR)
    )

    it_aa = (
        (DATA_TYPE.ADDR, DATA_TYPE.ADDR),
    )

    it_cap = (
        DATA_TYPE.INT, DATA_TYPE.ADDR, DATA_TYPE.PTR
    )

    it_ap = (
        DATA_TYPE.ADDR, DATA_TYPE.PTR
    )

    def __init__(self, lables: dict, unresolved: dict, ip: list) -> None:
        self.lables = lables
        self.unresolved = unresolved
        self.ip = ip

    def translate_size_postfix(self, postfix: str) -> int:
        return {'b': 1, 'w': 2, 'd': 4, 'q': 8}.get(postfix, 0)

    def resolve_op(self, op: str, lables: dict):
        op_type = DATA_TYPE.NONE

        if op[0] in string.digits + '-':
            op_type = DATA_TYPE.INT

            if op.startswith('0x'):
                value = int(op, 16)
            else:
                value = int(op)

        else:
            op_type = DATA_TYPE.ADDR

            if re.match('\(.*\)', op):
                op = op[1:-1]

            if re.match('\[.*\]', op):
                op_type = DATA_TYPE.PTR
                op = op[1:-1]

            op_expr = op.translate(
                {ord('-'): ' - ', ord('+'): ' + ', ord('*'): ' * '}
            ).split()

            for i in range(len(op_expr)):
                offset = lables.get(op_expr[i], -1)
                if offset != -1:
                    op_expr[i] = str(offset)

            value = eval(''.join(op_expr))

        return value, op_type

    def unresolve_op(self, op: str):
        op_type = DATA_TYPE.NONE

        if op[0] in string.digits + '-':
            op_type = DATA_TYPE.INT

            if op.startswith('0x'):
                value = int(op, 16)
            else:
                value = int(op)

        else:
            op_type = DATA_TYPE.ADDR

            if re.match('\(.*\)', op):
                op = op[1:-1]

            if re.match('\[.*\]', op):
                op_type = DATA_TYPE.PTR
                op = op[1:-1]

                op_expr = op.translate(
                    {ord('-'): ' - ', ord('+'): ' + ', ord('*'): ' * '}
                ).split()

                for i in range(len(op_expr)):
                    offset = self.lables.get(op_expr[i], -1)
                    if offset != -1:
                        op_expr[i] = str(offset)

                value = eval(''.join(op_expr))

            elif len(list(filter(lambda lit: lit in string.digits + '+*- ', op))) == len(op):
                value = eval(op)

            elif len(list(filter(lambda lit: lit in string.digits + string.ascii_letters + '_', op))) == len(op):
                unresolved = self.unresolved.get(op, [])
                unresolved.append(self.ip[0])
                self.unresolved[op] = unresolved
                value = 0

        return value, op_type

    def op_base(self, size: int, op1: str, op2: str, op: int, sizes: tuple,
                instr_types: tuple) -> bytes:
        op1, op1_type = self.resolve_op(op1, self.lables)
        op2, op2_type = self.resolve_op(op2, self.lables)

        instr_type = (op1_type, op2_type)

        if instr_type not in instr_types or size not in sizes:
            raise Exception('Invalid instruction operands or postfix!')

        instr_byte = op << 4
        instr_byte |= (instr_types.index(instr_type) << 2)
        instr_byte |= int(math.log(size, 2))
        instr_byte = struct.pack('B', instr_byte)

        op1 = pack_int(op1, ADDR_SIZE)

        if op2_type == DATA_TYPE.INT:
            op2 = pack_int(op2, size)
        else:
            op2 = pack_int(op2, ADDR_SIZE)

        return b''.join((instr_byte, op1, op2))

    def op_put_get(self, size: int, op1: str, op: int, sizes: tuple,
                   instr_types: tuple) -> bytes:
        op1, op1_type = self.resolve_op(op1, self.lables)

        instr_type = (op1_type)
        if instr_type not in instr_types or size not in sizes:
            raise Exception('Invalid instruction operands or postfix!')

        instr_byte = op << 4
        instr_byte |= instr_types.index(instr_type) << 2
        instr_byte |= int(math.log(size, 2))
        instr_byte = struct.pack('B', instr_byte)

        if op1_type == DATA_TYPE.INT:
            op1 = pack_int(op1, size)
        else:
            op1 = pack_int(op1, ADDR_SIZE)

        return b''.join((instr_byte, op1))

    def op_jmp(self, size: int, op1: str, op2: str, op: int, sizes: tuple,
               instr_types: tuple) -> bytes:
        op1, op1_type = self.unresolve_op(op1)
        op2, op2_type = self.resolve_op(op2, self.lables)

        instr_type = (op1_type, op2_type)
        if instr_type not in instr_types or size not in sizes:
            raise Exception('Invalid instruction operands or postfix!')

        instr_byte = op << 4
        instr_byte |= instr_types.index(instr_type) << 2
        instr_byte |= int(math.log(size, 2))
        instr_byte = struct.pack('B', instr_byte)

        op1 = pack_int(op1, ADDR_SIZE)

        if op2_type == DATA_TYPE.INT:
            op2 = pack_int(op2, size)
        else:
            op2 = pack_int(op2, ADDR_SIZE)

        return b''.join((instr_byte, op1, op2))

    def _exit(self, *args) -> bytes:
        return b'\x00'

    def _mov(self, *args) -> bytes:
        return self.op_base(*args, 0b0001, (1, 2, 4, 8), self.it_acaaappa)

    def _add(self, *args) -> bytes:
        return self.op_base(*args, 0b0010, (1, 2, 4, 8), self.it_acaaap)

    def _sub(self, *args) -> bytes:
        return self.op_base(*args, 0b0011, (1, 2, 4, 8), self.it_acaaap)

    def _mul(self, *args) -> bytes:
        return self.op_base(*args, 0b0100, (1, 2, 4, 8), self.it_acaaap)

    def _div(self, *args) -> bytes:
        return self.op_base(*args, 0b0101, (1, 2, 4, 8), self.it_acaaap)

    def _xor(self, *args) -> bytes:
        return self.op_base(*args, 0b0110, (1, 2, 4, 8), self.it_acaaap)

    def _and(self, *args) -> bytes:
        return self.op_base(*args, 0b0111, (1, 2, 4, 8), self.it_acaaap)

    def _or(self, *args) -> bytes:
        return self.op_base(*args, 0b1000, (1, 2, 4, 8), self.it_acaaap)

    def _rand(self, *args) -> bytes:
        return self.op_base(*args, 0b1001, (1, 2), self.it_acaaap)

    def _ror(self, *args) -> bytes:
        return self.op_base(*args, 0b1010, (1, 2, 4, 8), self.it_acaaap)

    def _rol(self, *args) -> bytes:
        return self.op_base(*args, 0b1011, (1, 2, 4, 8), self.it_acaaap)

    def _lea(self, *args) -> bytes:
        return self.op_base(*args, 0b1100, (2, ), self.it_aa)

    def _jmp(self, *args) -> bytes:
        return self.op_jmp(*args, 0b1101, (1, 2, 4, 8), self.it_acaaappa)

    def _put(self, *args) -> bytes:
        return self.op_put_get(*args, 0b1110, (1, ), self.it_cap)

    def _get(self, *args) -> bytes:
        return self.op_put_get(*args, 0b1111, (1, ), self.it_ap)


class UFOCompiler(object):
    def __init__(self, ufo_listing: str, verbosity: int = 0):
        self.listing = list(re.sub('\ {2,}', ' ', mnemon.replace(',', ' ')).strip() for mnemon in ufo_listing.split('\n'))
        self.verbosity = verbosity
        self.unresolved = {}
        self.code_lables = {}
        self.ip = [0]
        self.bytecode = []

        self.allocator = Allocator()
        self.assembler = Assembler(self.allocator.lables,
                                   self.unresolved,
                                   self.ip
                                   )

    def create_header(self, version: int, data_seg_offset: int,
                      entry_offset: int):
        return (b'UFOb' + struct.pack('<HHH', version,
                                      entry_offset,
                                      data_seg_offset)).ljust(0x10, b'\x00')

    def show_memory_map(self):
        print('MEMORY MAPPING')
        for alloc in self.allocator.memory_map:
            log = 'offset {0:04x} | {1}'.format(
                alloc.offset,
                ' '.join('{:02x}'.format(b) for b in alloc.data))

            print(log)

    def show_lables(self):
        print('LABLES')
        for lable, offset in self.allocator.lables.items():
            print('offset {0:04x} | name={1}'.format(offset, lable))

    def compile(self):
        if self.verbosity > 1:
            print('ASSEMNLY')

        self.current_seg = SEGMENT.NONE

        for line, mnemon in enumerate(self.listing, 1):
            mnemon = mnemon.split('#')[0].strip()
            if not mnemon:
                continue

            if mnemon[0] == '.':
                self.current_seg = SEGMENT.name2id[mnemon]
                continue

            if mnemon[-1] == ':' and self.current_seg == SEGMENT.CODE:
                if self.code_lables.get(mnemon[:-1], -1) != -1:
                    raise Exception('Code lable already exist!')

                self.code_lables[mnemon[:-1]] = self.ip[0]
                continue

            if self.current_seg == SEGMENT.NONE:
                raise Exception(f'Uninitialized segment at line {line}.')

            try:
                if self.current_seg == SEGMENT.CODE:
                    self.assembly(mnemon)

                    if self.verbosity > 1:
                        log = 'line={0} | offset={1:04x} | {2} | {3}'.format(
                            line,
                            sum(map(len, self.bytecode)),
                            mnemon,
                            ' '.join('{:02x}'.format(b) for b in self.bytecode[-1]))

                        print(log)

                else:
                    self.allocator.alloc(mnemon)

            except Exception:
                raise Exception(f'Сaught exception at line {line}.\n\n')

        self.bytecode.append(b'\x00')

        if self.unresolved:
            offset = 0
            rest = list(self.code_lables.items())
            for i, bc in enumerate(self.bytecode):
                if not rest:
                    break

                if i == rest[0][1]:
                    self.code_lables[rest[0][0]] = offset
                    rest.pop(0)

                offset += len(bc)

            for name, ibs in self.unresolved.items():
                lookup = self.code_lables.get(name, -1)
                if lookup == -1:
                    raise Exception(f'Unresolved code lable: {name}')

                for ib in ibs:
                    bc = bytearray(self.bytecode[ib])
                    bc[1:3] = pack_int(lookup, ADDR_SIZE)
                    self.bytecode[ib] = bc

        if self.verbosity > 0:
            if self.verbosity > 1:
                print()

            self.show_memory_map()
            print()
            self.show_lables()

        self.bytecode = b''.join(self.bytecode)

        if len(self.bytecode) % 16 != 0:
            width = len(self.bytecode) - len(self.bytecode) % 16 + 16
            self.bytecode = self.bytecode.ljust(width, b'\x00')

        data_seg_offset = 0x10 + len(self.bytecode)
        entry_point = 0x10 + self.code_lables.get('start')
        header = self.create_header(1, data_seg_offset, entry_point)
        data_seg = self.allocator.get_raw_memory_map()

        return b''.join((header, self.bytecode, data_seg))

    def assembly(self, instr: str):
        tokens = instr.split()
        instr = tokens[0][:-1]

        handler = getattr(Assembler, '_'+instr)
        if not handler:
            raise Exception(f'Invalid instruction: {instr}!')

        instr_size = self.assembler.translate_size_postfix(tokens[0][-1])

        if not instr_size:
            raise Exception('Invalid instruction size postfix!')

        self.bytecode.append(handler(self.assembler, instr_size, *tokens[1:]))
        self.ip[0] += 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(USAGE_BANNER)
        exit(1)

    verbosity = 0
    if len(sys.argv) > 3:
        verbosity = int(sys.argv[3])

    ufo_file = sys.argv[1]
    output_file = sys.argv[2]

    compiler = UFOCompiler(open(ufo_file).read(), verbosity=verbosity)
    bytecode = compiler.compile()

    with open(output_file, 'wb') as file:
        file.write(bytecode)

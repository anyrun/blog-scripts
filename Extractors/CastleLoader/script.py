# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# please, check out README.md before using this

import argparse, struct, lief, sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

lief.logging.disable()

# Pre-compiled struct for DWORD unpacking
_DWORD = struct.Struct('<I')
_MAX_FOUNDS = 52

# CastleLoader XOR algorithm
def Xor(data, key):
    raw = b''.join(_DWORD.pack(num) for num in data)
    key_len = len(key)
    decoded = bytearray()

    for i in range(0, len(raw), 2):
        low_byte = raw[i]
        high_byte = raw[i + 1] if i + 1 < len(raw) else 0

        if low_byte == 0 and high_byte == 0:
            continue

        decoded.append(low_byte ^ key[(i >> 1) % key_len])
        decoded.append(high_byte)

    return decoded.decode('utf-16le', errors='ignore').rstrip('\x00')

# Finds and decrypts config string by locating MOV stack-write pattern, collecting DWORDs, extracting XOR key from .data access
def ParseNext(data: bytes, pe, cs, start_offset: int):
    data_len = len(data)
    mv = memoryview(data)

    found_mov = data.find(b'\xC7', start_offset)
    if found_mov == -1 or found_mov >= data_len - 1:
        return None, data_len

    modrm = data[found_mov + 1]
    if modrm not in (0x45, 0x85):
        return None, found_mov + 1

    config_data = []
    array_offset = found_mov
    key = None

    while array_offset < data_len - 10:
        try:
            # Disassemble one instruction at current offset
            code = data[array_offset:array_offset + 15]  # Max x86 instruction is 15 bytes
            insn = next(cs.disasm(code, array_offset, 1), None)
            if not insn:
                array_offset += 1
                continue

            insn_len = insn.size
            insn_mnemonic = insn.mnemonic.upper()

            # Clear config on RET/CALL (garbage)
            if len(config_data) < 10 and insn_mnemonic in ('RET', 'CALL'):
                if config_data:
                    break
                config_data.clear()
                array_offset += insn_len
                continue

            # Clear config on any jump instruction (garbage)
            if insn_mnemonic[0] == 'J':
                if config_data:
                    break
                config_data.clear()
                array_offset += insn_len
                continue

            b1, b2 = data[array_offset], data[array_offset + 1]

            # Key pattern (0F B6 80) - MOVZX reading from .data section
            if b1 == 0x0F and b2 == 0xB6 and data[array_offset + 2] == 0x80:
                key_va = _DWORD.unpack(mv[array_offset + 3:array_offset + 7])[0]
                try:
                    key = pe.get_content_from_virtual_address(key_va, 4).tobytes()
                    if len(key) == 4:
                        break
                    key = None
                except Exception:
                    pass

            # MOV [EBP-X], imm32 (C7 45) - write dword ptr to stack
            elif b1 == 0xC7 and b2 == 0x45:
                config_data.append(_DWORD.unpack(mv[array_offset + 3:array_offset + 7])[0])

            # MOV [EBP-X], imm32 (C7 85) - write dword ptr to stack
            elif b1 == 0xC7 and b2 == 0x85:
                config_data.append(_DWORD.unpack(mv[array_offset + 6:array_offset + 10])[0])

            array_offset += insn_len

        except Exception:
            array_offset += 1

    if config_data and key:
        try:
            string = Xor(config_data, key)
            if len(string) > 1:
                return string, array_offset
        except Exception:
            pass

    return None, found_mov + 1

# Extract configuration string by pattern (re)
def ExtractConfigByPattern(data: bytes, pe, cs, pattern):
    match = pattern.search(data)
    if not match:
        return None

    offset = match.start()

    result, _ = ParseNext(data, pe, cs, offset)
    if result:
        return result

    return None

# Extract all configuration strings
def ExtractAllConfigs(data: bytes, pe, cs):
    results = []
    current_offset = 0
    data_len = len(data)

    while current_offset < data_len:
        if len(results) >= _MAX_FOUNDS:
            break

        result, next_offset = ParseNext(data, pe, cs, current_offset)

        if result:
            results.append(result)

        current_offset = next_offset

    print(f"[+] Done. Found {len(results)} strings")
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dump', help='Path to memory dump file')
    args = parser.parse_args()

    try:
        with open(args.dump, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"[-] Error reading file: {e}")
        sys.exit(1)

    pe = lief.parse(data)
    if not pe:
        print("[-] Failed to parse PE file")
        sys.exit(1)

    # Initialize capstone disassembler for x86 32-bit
    cs = Cs(CS_ARCH_X86, CS_MODE_32)

    result = ExtractAllConfigs(data, pe, cs)
    print(result)

    # Find mutex only (works for MD5 1E0F94E8EC83C1879CCD25FEC59098F1, config layout and
    # decryption routines differ across binaries, so patterns vary)

    # pattern = re.compile(
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\x33\xC9'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\xC7\x45.{5}'
    #     b'\x66\x89\x45.'
    #     b'\x0F\x1F\x44\x00.'
    #     b'\x8B\xC1'
    #     b'\x83\xE0.'
    #     b'\x0F\xB6\x80.{4}'
    #     b'\x66\x33\x44\x4D.'
    #     b'\x66\x89\x84\x4D',
    #     re.DOTALL
    # )
    #
    # mutex = ExtractConfigByPattern(data, pe, cs, pattern)
    # print(mutex)

if __name__ == '__main__':
    main()
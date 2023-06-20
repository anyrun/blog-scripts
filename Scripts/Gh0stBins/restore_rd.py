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

# This script extracts malicious RDP module from the traffic

import re, struct, zlib

FILENAME = 'traffic/kernel_traffic_dump.bin'
OUT_FILENAME = 'traffic/rd_restored.bin'
FILTER = rb'\x42\x49\x4E\x53'
HEADER_SZ = 16

def get_hash(pp: bytes) -> int:
    hash = 0
    for i in range(len(pp)):
        hash += pp[i]
    return hash

stream = b''
with open(FILENAME, 'rb') as f:
    stream = f.read()

matches = re.search(FILTER, stream)
offset = matches.start()

excepted_hash = None
excepted_sz = None
total_hash = 0
constructed_rd = b''
while offset < len(stream):
    magic, pkt_sz, payload_sz, pkt_type = struct.unpack(b'<IIII', stream[offset:offset+16])
    assert stream[offset:offset+4] == b'BINS'

    if pkt_sz and payload_sz and pkt_type != 0xABCDEF:
        assert stream[offset+HEADER_SZ:offset+HEADER_SZ+2] == b'\x78\x9c'

        payload = zlib.decompress(stream[offset+HEADER_SZ:offset+HEADER_SZ+pkt_sz])
        if len(payload) > 10:
            command, total_sz, curr_sz = struct.unpack(b'<HII', payload[:10])
            if command == 0xfa01:
                pp = payload[10:-4]
                pp_calc_hash = get_hash(pp)
                #print(hex(pp_calc_hash))
                pp_hash = int.from_bytes(payload[-4:], 'little')
                #print(hex(pp_hash))
                assert pp_hash == pp_calc_hash

                total_hash += pp_calc_hash
                constructed_rd += pp

            elif command == 0xea07:
                assert excepted_sz == None and excepted_hash == None \
                    and constructed_rd == b'' and total_hash == 0
                excepted_sz = total_sz
                print(f'[+] Expected payload size: 0x{excepted_sz:08x}')
                excepted_hash = curr_sz
                print(f'[+] Expected payload hash: 0x{excepted_hash:08x}')

    offset += HEADER_SZ + pkt_sz

assert len(constructed_rd) == excepted_sz
assert excepted_hash == get_hash(constructed_rd)
print('[+] Done')

with open(OUT_FILENAME, 'wb') as f:
   f.write(constructed_rd)
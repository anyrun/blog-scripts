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

# This script restores a video stream

import re

FILENAME = 'traffic/rdp_dump.bin'
OUT_FILENAME = 'traffic/rdp_dump_concat.bin'
FILTER = rb'\x42\x49\x4E\x53...\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa2\xaa\x00\x00\x00'

stream = b''
with open(FILENAME, 'rb') as f:
    stream = f.read()

matches = re.search(FILTER, stream)
offset = matches.start()

i = 0
constructed_stream = b''
while offset < len(stream):
    assert stream[offset:offset+4] == b'BINS'
    assert stream[offset+16:offset+20] == b'\xa2\xaa\x00\x00'
    sz = int.from_bytes(stream[offset+4:offset+8], 'little')
    payload = stream[offset+18:offset+18+sz-2]
    constructed_stream += payload
    offset += 16 + sz
    i+= 1

with open(OUT_FILENAME, 'wb') as f:
    f.write(constructed_stream)

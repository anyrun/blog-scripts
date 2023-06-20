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

# This is a FAKE-HTTP server to develop network signatures for detecting Gh0stBins

import socket, zlib, struct

LISTEN_ADDR = '10.37.129.2'
LISTEN_PORT = 10086

HEADER_REG = b'KNEL'
HEADER_RESP = b'BINS'

class PacketType:
    heart_beat = 0xABCDEF
    data = 0x0

class Packet:
    magic = HEADER_RESP
    data = None
    c_data = None
    data_len = 0

    fmt_header = b'@4sIII'

    def __init__(self, data: bytes, out: bool = False):
        if not out:
            if len(data) == 4 and data == b'KNEL':
                self.magic = HEADER_REG
                return

            hdr = data[:16]
            fields = struct.unpack(self.fmt_header, hdr)
            (
                self.magic,
                self.pkt_len,
                self.data_len,
                self.t
            ) = fields

            if len(data) > 16:
                self.c_data = data[16:]
                self.data = zlib.decompress(self.c_data)
                assert len(self.data) == self.data_len
        else:
            if not len(data):
                self.t = PacketType.heart_beat
            else:
                self.t = PacketType.data

            self.data = data

            self.c_data = zlib.compress(data)
            self.data_len = len(data)
            self.pkt_len = len(self.c_data)

    def pack(self) -> bytes:
        return struct.pack(self.fmt_header, self.magic, self.pkt_len, self.data_len, self.t) + self.c_data

    def __bytes__(self):
        return self.pack()

    def __repr__(self):
        return str(self.data)

    def unpack(self) -> bytes:
        return self.data

test_case_1 = bytes(Packet(b'RE', True))
test_case_2 = bytes.fromhex('42494E530A0000000200000000000000789C0B72050000EB0098')
assert test_case_1 == test_case_2

def main() -> None:
    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set socket options
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the address and port
    server_socket.bind((LISTEN_ADDR, LISTEN_PORT))

    # Start listening for incoming connections
    server_socket.listen()
    print(f'[INFO] Server is listening at {LISTEN_ADDR}:{LISTEN_PORT}...')

    try:
        client_socket, client_address = server_socket.accept()
        print(f"[INFO] New connection from {client_address}")

        done = False
        while True:
            data = client_socket.recv(4096)
            pkt = Packet(data)
            if pkt.magic == b'KNEL':
                print('[INFO] Registration request')
                client_socket.send(bytes(Packet(b'RE', True)))
                print('[INFO] Registration request confirmed')
                continue

            elif pkt.magic == b'BINS' and pkt.t == int(PacketType.heart_beat):
                print('[INFO] Heartbeat received')

            elif pkt.magic == b'BINS' and pkt.t == int(PacketType.data):
                print('[INFO] Data received')
                print(pkt.unpack())

            else:
                raise ValueError(f'[ERROR] Unknown data: {data}')

            client_socket.send(bytes(Packet(b'', True)))
            print('[INFO] Heartbeat answer sent')

            #if not done:
                #done = True
                #time.sleep(3)
                #client_socket.send(bytes(Packet(b'\x0b\xdd', True)))
                #pkt = Packet(client_socket.recv(4096))
                #print(pkt.unpack())

    except Exception as e:
        print(f'[ERROR] {e}')

    client_socket.close()
    print(f"[INFO] Server stopped. Bye!")

if __name__ == "__main__":
    main()

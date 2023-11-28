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

# This is a sample script that decrypts raw TCP stream dumps into readable JSON.
# To obtain a dump:
#   1. Download the PCAP file from the task at any.run.
#   2. Open it with Wireshark.
#   3. Select any packet from the target stream (for example, try filtering packets using "tcp.port eq 50500" or streams with "tcp.stream eq 0").
#   4. Right-click on the selected packet > Follow > TCP Stream.
#   5. From the list labeled "Show data as," select "Raw."
#   6. Click "Save as..."

from base64 import b64encode

import sys, json, os


PACKET_TYPES = {
	0x2710: "SERVER_PING",
	0x2711: "CLIENT_PING",
	0x2712: "SERVER_INIT",
	0x2713: "SET_TIMEOUT",
	0x2714: "CLIENT_REQUEST_FILE",
	0x2715: "SERVER_SEND_FILE",
	0x2716: "CLIENT_CONFIRM_IP",
	0x2717: "SERVER_SEND_MARKS",
	0x2718: "CLIENT_CONFIRM_MARKS",
	0x2719: "SERVER_SEND_GRAB_CONFIG",
	0x271A: "CLIENT_CONFIRM_GRAB_CONFIG",
	0x271B: "SERVER_SEND_LOADER_CONFIG",
	0x271C: "CLIENT_CONFIRM_LOADER_CONFIG",
	0x271D: "SERVER_SET_FILE_FILTER",
	0x271E: "CLIENT_CONFIRM_LOADER_EXECUTION",
	0x271F: "CLIENT_SEND_FILE",
	0x2720: "CLIENT_INIT",
	0x2721: "SERVER_SEND_IP",
	0x2722: "CLIENT_SEND_UNKNOWN",
	0x2723: "SERVER_SEND_UNKNOWN",
	0x2724: "SERVER_SEND_HWID",
	0x272B: "SERVER_SEND_FORCE_QUIT"
}


# substitution cipher

# \xFF\x01\x55\x0A\x00\xDE\xFD\x80\x05 -> \x55\x05\x00\x01\x80\xFD\xFF\x0A\xDE


MAPPING_TABLE = {
	0xFF: 0x55,
	0x01: 0x05,
	0x55: 0x00,
	0x0A: 0x01,
	0x00: 0x80,
	0xDE: 0xFD,
	0xFD: 0xFF,
	0x80: 0x0A,
	0x05: 0xDE,
}


def decrypt_payload(payload: bytearray, key: int):
	for i in range(len(payload)):
		b = payload[i]
		if b in MAPPING_TABLE:
			payload[i] = MAPPING_TABLE[b]
		payload[i] ^= key


def client_to_server_file_handler(payload: bytearray):
	file_name = payload[:100].strip(b"\x00").decode()
	arg_1 = payload[100:200].strip(b"\x00").decode()
	arg_2 = payload[200:300].strip(b"\x00").decode()
	file_bytes = payload[300:]

	return {
		"filename": file_name,
		"arg_1": arg_1,
		"arg_2": arg_2,
		"file_bytes": b64encode(file_bytes).decode(),
	}


def server_to_client_file_handler(payload: bytearray):
	file_name = payload[:100].strip(b"\x00").decode()
	file_bytes = payload[100:]

	return {"filename": file_name, "file_bytes": b64encode(file_bytes).decode()}


def config_handler(payload: bytearray):
	return json.loads(payload.decode())


def default_handler(payload: bytearray):
	try:
		return payload.decode()

	except:
		return b64encode(payload).decode()


HANDLERS = {
	0x2715: server_to_client_file_handler,
	0x271F: client_to_server_file_handler,
	0x2719: config_handler,
	0x2717: config_handler,
	0x271B: config_handler,
	0x271D: config_handler,
}

def main():
	xor_key = 0x36
	port = "50500"

	if len(sys.argv) < 4:
		filename = os.path.basename(sys.argv[0])
		print(f"Usage: {filename} <path_to_tcp_stream_dump> <path_to_json_output> [<port>]")
		print(f"Example: {filename} risepro_tcp_dump.bin risepro_tcp_parsed.json 50505")
		exit(0)

	in_file = sys.argv[1]
	out_file = sys.argv[2]
	if len(sys.argv) > 3:
		port = sys.argv[3]


	if port == "50505":
		xor_key = 0x79
	elif port == "50500":
		pass # using default
	else:
		print(f'Unknown port, trying default key {hex(xor_key)}')

	if port != "50500":
		print(f"Packets may have different meaning and structure for {port}, be aware")

	result = []


	with open(in_file, "rb") as f:
		packet = f.read()


	while packet.startswith(b"\xAD\xDA\xBA\xAB"):
		packet_length = int.from_bytes(packet[4:8], "little")
		packet_type = int.from_bytes(packet[8:12], "little")
		packet_type_str = PACKET_TYPES[packet_type] if packet_type in PACKET_TYPES else "UNKNOWN_PACKET_TYPE"

		if packet_type not in PACKET_TYPES:
			print(f"Unknown packet {hex(packet_type)}")

		packet_payload = bytearray(packet[12 : packet_length + 12])
		decrypt_payload(packet_payload, xor_key)
		handler = HANDLERS[packet_type] if packet_type in HANDLERS else default_handler
		try:
			payload = handler(packet_payload)
		except:
			payload = default_handler(packet_payload)
		result.append(
			{
				"code": hex(packet_type),
				"type": packet_type_str,
				"payload_size": packet_length,
				"payload": payload,
			}
		)

		packet = packet[packet_length + 12:]

		if len(packet) > 0 and not packet.startswith(b"\xAD\xDA\xBA\xAB"):
			print(f"Last {len(packet)} bytes were not processed (maybe due to misalignment)")


	with open(out_file, "w") as f:
		json.dump(result, f)


if __name__ == "__main__":
	main()
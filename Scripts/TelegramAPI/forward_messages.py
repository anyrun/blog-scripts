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

# This script will forward messages in specified range, splitting it in chunks of 100 messages maximum
#
# To use this script:
#	1. Find bot token, src_chat_id (from which messages will be forwarded) and dest_chat_id (to which to forward); latter can be obtained by prepare_bot.py
#	2. Run script with token, src_chat_id and dest_chat_id as arguments
#
#	Additional parameters:
#		start_message_id - id of first message to forward, default 1
#		end_message_id - id of last message to forward, default 2^32
#		sleep_time_seconds - delay between requests to Telegram API, default 3 seconds (i.e. ~20 requests per minute)
#		responses_directory - the location where server responses will be stored as separate JSON files; if directory doesn't exist, it will be created
#		http_429_handling - strategy of "Too Many Requests" error handling, available values: wait, stop; default - wait

import argparse, requests, os, json
from time import sleep
from datetime import datetime, timedelta


def make_request(token, message_ids: list[int], dst, src):
	return requests.get(f"https://api.telegram.org/bot{token}/forwardMessages?chat_id={dst}&from_chat_id={src}&message_ids={json.dumps(message_ids)}").json()


def main():
	parser = argparse.ArgumentParser(description="This script will forward messages in specified range, splitting it in chunks of 100 messages maximum")
	parser.add_argument("telegram_bot_token")
	parser.add_argument("src_chat_id", help="ID of the chat, from which messages will be forwarded")
	parser.add_argument("dest_chat_id", help="ID of the chat, to which messages will be forwarded")
	parser.add_argument("--start_message_id", "--start", "-s", default=1, type=int, help="ID of first message to forward")
	parser.add_argument("--end_message_id", "--end", "-e", default=2**32, type=int, help="ID of last message to forward")
	parser.add_argument("--sleep_time_seconds", "--sleep", "-t", default=3, type=float, help="delay between requests to Telegram API")
	parser.add_argument("--responses_directory", "--responses", "-o", default="responses", help="the location where server responses will be stored as separate JSON files")
	parser.add_argument("--http_429_handling", "--handle", default="wait", choices=["wait", "stop"], help="strategy of \"Too Many Requests\" error handling")
	
	args = parser.parse_args()

	token = args.telegram_bot_token.removeprefix("bot")
	src_chat_id = args.src_chat_id
	dest_chat_id = args.dest_chat_id
	current_message_id = args.start_message_id
	end_message_id = args.end_message_id
	responses_dir = args.responses_directory
	sleep_time = args.sleep_time_seconds
	http_429_handling = args.http_429_handling

	if not os.path.exists(responses_dir):
		os.mkdir(responses_dir)

	t = datetime.now()
	print(f"[{t}] Starting with next settings:")
	print(f"\tBot token: {token}")
	print(f"\tSource chat id: {src_chat_id}")
	print(f"\tDestination chat id: {dest_chat_id}")
	print(f"\tStart message id: {current_message_id}")
	print(f"\tEnd message id: {end_message_id}")
	print(f"\tSleep time (seconds): {sleep_time}")
	print(f"\tResponses directory: {responses_dir}")
	print(f"\tHTTP 429 code handling: {http_429_handling}")

	while current_message_id <= end_message_id:
		print()
		t = datetime.now()
		messages_end = current_message_id + 100 if end_message_id == -1 else min(current_message_id + 100, end_message_id + 1)
		print(f"[{t}] Forwarding messages with id [{current_message_id}-{messages_end - 1}]")
		response = make_request(token, list(range(current_message_id, messages_end)), dest_chat_id, src_chat_id)
		with open(os.path.join(responses_dir, f"forward_messages_from_{src_chat_id}_to_{dest_chat_id}_{current_message_id}_{messages_end}.json"), "w") as f:
			json.dump(response, f)
		if not response["ok"]:
			error_code = response["error_code"]
			t = datetime.now()
			if error_code == 429:
				if http_429_handling == "wait":
					retry_after = response["parameters"]["retry_after"]
					end_t = t + timedelta(seconds=retry_after)
					print(f"[{t}] HTTP 429, waiting for [{end_t}] ({retry_after} seconds)...")
					sleep(retry_after)
					continue
				print(f"[{t}] HTTP 429, break")
			elif error_code == 400 and response["description"] == "Bad Request: there are no messages to forward":
				print(f"[{t}] HTTP 400, messages not found, skip...")
				current_message_id += 100
				sleep(sleep_time)
				continue
			print(f"[{t}] Unhandled error:\n{json.dumps(response, indent=1)}")
			break

		t = datetime.now()
		print(f"[{t}] Forwarded", len(response["result"]), "messages")
		current_message_id += 100
		sleep(sleep_time)


if __name__ == "__main__":
	main()

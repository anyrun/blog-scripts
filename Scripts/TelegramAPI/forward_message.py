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

# This script will forward messages one by one from one chat to another
#
# To use this script:
#	1. Find bot token, src_chat_id (from which messages will be forwarded) and dest_chat_id (to which to forward); latter can be obtained by prepare_bot.py
#	2. Run script with token, src_chat_id and dest_chat_id as arguments
#
#	Additional parameters:
#		start_message_id - id of first message to forward, default 1
#		end_message_id - id of last message to forward, default -1 (i.e. no end message)
#		sleep_time_seconds - delay between requests to Telegram API, default 3 seconds (i.e. ~20 requests per minute)
#		responses_directory - the location where server responses will be stored as separate JSON files; if directory doesn't exist, it will be created
#		http_429_handling - strategy of "Too Many Requests" error handling, available values: wait, stop; default - wait

import sys, requests, os, json
from time import sleep
from datetime import datetime, timedelta

def make_request(token, message_id, dst, src):
	return requests.get(f"https://api.telegram.org/bot{token}/forwardMessage?chat_id={dst}&from_chat_id={src}&message_id={message_id}").json()


def main():
	if len(sys.argv) < 4:
		print("Usage:", sys.argv[0], "<telegram_bot_token> <dest_chat_id> <src_chat_id>\n\t[<start_message_id>=1] [<end_message_id>=-1] [<sleep_time_seconds>=3] [<responses_directory>=responses] [<http_429_handling>:{wait,stop}=wait]")
		return

	token = sys.argv[1]
	if token.startswith("bot"):
		token = token[3:]
	
	dest_chat_id = sys.argv[2]
	src_chat_id = sys.argv[3]

	other_settings = {
		"start_message_id": 1,
		"end_message_id": -1,
		"sleep_time_seconds": 3,
		"responses_directory": "responses",
		"http_429_handling": "wait"
	}

	if len(sys.argv) > 4:
		other_settings.update(dict(zip(["start_message_id", "end_message_id", "sleep_time_seconds","responses_directory", "http_429_handling"], sys.argv[4:])))
	
	current_message_id = int(other_settings["start_message_id"])
	end_message_id = int(other_settings["end_message_id"])
	check_lambda = (lambda id: current_message_id <= end_message_id) if end_message_id != -1 else (lambda id: True)
	responses_dir = os.path.abspath(other_settings["responses_directory"])
	sleep_time = int(other_settings["sleep_time_seconds"])
	http_429_handling = other_settings["http_429_handling"]
	if not http_429_handling in ["wait", "stop"]:
		http_429_handling = "stop"


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

	while check_lambda(current_message_id):
		print()
		t = datetime.now()
		print(f"[{t}] Forwarding message with id [{current_message_id}]")
		response = make_request(token, current_message_id, dest_chat_id, src_chat_id)
		with open(os.path.join(responses_dir, f"forward_message_from_{src_chat_id}_to_{dest_chat_id}_{current_message_id}.json"), "w") as f:
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
			elif error_code == 400 and response["description"] == "Bad Request: message to forward not found":
				print(f"[{t}] HTTP 400, message not found, skip...")
				current_message_id += 1
				sleep(sleep_time)
				continue
			print(f"[{t}] Unhandled error: {json.dumps(response, indent=1)}")
			break
		

		
		current_message_id += 1
		sleep(sleep_time)


if __name__ == "__main__":
	main()
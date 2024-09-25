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

# This script will delete messages one by one
#
# To use this script:
#	1. Find bot token and chat_id (from which messages will be deleted)
#	2. Run script with token and chat_id as arguments
#
#	Additional parameters:
#		start_message_id - id of first message to delete, default 1
#		end_message_id - id of last message to delete, default 2^32
#		sleep_time_seconds - delay between requests to Telegram API, default 3 seconds (i.e. ~20 requests per minute)
#		responses_directory - the location where server responses will be stored as separate JSON files; if directory doesn't exist, it will be created
#		http_429_handling - strategy of "Too Many Requests" error handling, available values: wait, stop; default - wait


import argparse, requests, os, json
from time import sleep
from datetime import datetime, timedelta


def make_request(token, message_id, dst):
	return requests.get(f"https://api.telegram.org/bot{token}/deleteMessage?chat_id={dst}&message_id={message_id}").json()


def main():
	parser = argparse.ArgumentParser(description="This script will delete messages one by one")
	parser.add_argument("telegram_bot_token")
	parser.add_argument("chat_id", help="ID of the chat, from which messages will be deleted")
	parser.add_argument("--start_message_id", "--start", "-s", default=1, type=int, help="ID of first message to delete")
	parser.add_argument("--end_message_id", "--end", "-e", default=2**32, type=int, help="ID of last message to delete")
	parser.add_argument("--sleep_time_seconds", "--sleep", "-t", default=3, type=float, help="delay between requests to Telegram API")
	parser.add_argument("--responses_directory", "--responses", "-o", default="responses", help="the location where server responses will be stored as separate JSON files")
	parser.add_argument("--http_429_handling", "--handle", default="wait", choices=["wait", "stop"], help="strategy of \"Too Many Requests\" error handling")
	
	args = parser.parse_args()

	token = args.telegram_bot_token.removeprefix("bot")
	chat_id = args.chat_id
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
	print(f"\tChat id: {chat_id}")
	print(f"\tStart message id: {current_message_id}")
	print(f"\tEnd message id: {end_message_id}")
	print(f"\tSleep time (seconds): {sleep_time}")
	print(f"\tResponses directory: {responses_dir}")
	print(f"\tHTTP 429 code handling: {http_429_handling}")

	while current_message_id <= end_message_id:
		print()
		t = datetime.now()
		print(f"[{t}] Deleting message with id [{current_message_id}]")
		response = make_request(token, current_message_id, chat_id)
		with open(os.path.join(responses_dir, f"delete_message_{chat_id}_{current_message_id}.json"), "w") as f:
			json.dump(response, f)

		
		t = datetime.now()
		message = f"[{t}] Message has been deleted successfully"
		wait = sleep_time
		if not response["ok"]:
			error_code = response["error_code"]
			handled = False

			if error_code == 429:
				if http_429_handling == "wait":
					retry_after = response["parameters"]["retry_after"]
					end_t = t + timedelta(seconds=retry_after)
					message = f"[{t}] HTTP 429, waiting for [{end_t}] ({retry_after} seconds)..."
					wait = retry_after
					handled = True
				else:
					message = f"[{t}] HTTP 429, break"
			elif error_code == 400:
				desc = response["description"]
				if desc in ["Bad Request: message to delete not found", "Bad Request: message can't be deleted for everyone"]:
					handled = True
					message = f"[{t}] {desc}"
				else:
					message = None
			
			if not handled:
				print(message or f"[{t}] Unhandled error: {json.dumps(response, indent=1)}")
				break
		
		print(message)
		current_message_id += 1
		sleep(wait)


if __name__ == "__main__":
	main()

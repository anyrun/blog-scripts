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

# To use this script:
#	1. Find bot token
#	2. Run script with token as argument
#	3. Find bot by username
#	4. After message "Now waiting for updates..." add bot to group chat (preferred) or send it a message (not recommended)
#	5. Copy chat id to use it as dest_chat_id in forward_message(s).py


import argparse, requests, json
from time import sleep


def ask_yn(question: str, default: bool = False):
	choice = " (Y/n):" if default else " (y/N):"
	choice = input(question + choice)
	if default:
		return choice not in ["N", "n"]
	else:
		return choice in ["Y", "y"]

def erase_updates(token):
	last_update = get_last_update(token)
	last_update = last_update["result"][0]
	update_id = last_update["update_id"]
	requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset={int(update_id) + 1}")
	return last_update

def get_last_update(token):
	return requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1").json()

def extract_chat_id(response):
	if "chat" in response:
		return response["chat"]["id"]
	
	for k, v in response.items():
		if type(v) == dict and "chat" in v:
			return v["chat"]["id"]
	
	return None

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("telegram_bot_token")

	args = parser.parse_args()
	token = args.telegram_bot_token.removeprefix("bot")
	
	bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()["result"]
	if not bot_info["can_join_groups"] and not ask_yn("Bot can't join groups, continue?"):
		return
	print()
	print("Use this data to find bot in Telegram:")
	print("Bot username:", bot_info["username"])
	print("Bot title:", bot_info["first_name"])
	print()
	print("Checking webhook...")
	webhook_info = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo").json()
	webhook_url = webhook_info["result"]["url"]
	delete_and_restore = False
	if webhook_url:
		print(f"Found webhook:\n{json.dumps(webhook_info, indent=1)}")
		delete_and_restore = ask_yn("Try delete and restore?")
		if not delete_and_restore:
			return
		if webhook_info["result"]["has_custom_certificate"]:
			print("WARNING: webhook has custom certificate, which will be lost!")
		print("WARNING: existing webhook will be deleted and restored, but secret token may be lost!")
		print("WARNING: if existing webhook has custom ip, it will be lost!")
		if not ask_yn("Continue anyway?"):
			return
	else:
		print("Checking if any updates already present...")
		updates = requests.get(f"https://api.telegram.org/bot{token}/getUpdates").json()
		if updates["result"]:
			print("Found", len(updates["result"]), "pending updates")
			if ask_yn("Erase them?", True):
				erase_updates(token)
			else:
				return

	if delete_and_restore:
		requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

	chat_id = None

	try:
		print("Now waiting for updates...")
		last_update = get_last_update(token)
		while not last_update["result"] or (chat_id := extract_chat_id(last_update["result"][0])) == None:
			sleep(3)
			last_update = get_last_update(token)
		
		print("Got update, erasing...")
		erase_updates(token)
	finally:
		if delete_and_restore:
			print("Restoring webhook...")
			webhook_info = webhook_info["result"]
			new_webhook = {
				"url": webhook_info["url"], 
				"max_connections": webhook_info["max_connections"], 
				}
			if "allowed_updates" in webhook_info:
				new_webhook["allowed_updates"] = webhook_info["allowed_updates"]
			requests.post(f"https://api.telegram.org/bot{token}/setWebhook", json=new_webhook)
		
	print("Bot prepared, your chat id:", chat_id)


if __name__ == "__main__":
	main()
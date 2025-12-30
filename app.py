import os
import time
import json
import requests
import logging
import re
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
STATE_FILE = os.getenv("STATE_FILE", "/data/state.json")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "octoping"
}

def load_state():
    if not os.path.exists(STATE_FILE):
        logging.info("State file does not exist, starting fresh")
        return None
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        ts = datetime.fromisoformat(data["last_seen"])
        logging.info(f"Loaded last seen timestamp: {ts}")
        return ts

def save_state(ts):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_seen": ts.isoformat()}, f)
    logging.info(f"Saved last seen timestamp: {ts}")

def fetch_notifications():
    logging.info("Fetching notifications from GitHub")
    r = requests.get(
        "https://api.github.com/notifications",
        headers=HEADERS,
        params={"all": "false"}
    )
    r.raise_for_status()
    notifications = r.json()
    logging.info(f"Fetched {len(notifications)} notifications")
    return notifications

def send_webhook(notification):
    logging.info(f"Sending webhook for notification {notification['id']}: {notification['subject']['title']}")
    
    # Create markdown summary (single line)
    repo = notification["repository"]["full_name"]
    title = notification["subject"]["title"]
    type = notification["subject"]["type"]
    reason = notification["reason"]
    url = notification.get("html_url", notification["subject"]["url"])
    
    markdown = "{} {}: {}{}".format(
        re.sub(r'(?<!^)(?=[A-Z])', ' ', type),
        reason.capitalize(),
        title,
        f" - [🔗]({url})" if url else ""
    )
    
    payload = {
        "id": notification["id"],
        "reason": notification["reason"],
        "updated_at": notification["updated_at"],
        "repository": notification["repository"]["full_name"],
        "subject": notification["subject"],
        "url": url,
        "markdown": markdown,
        "raw": notification,
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)
    logging.info(f"Webhook sent successfully for notification {notification['id']}")

def main():
    logging.info("Starting octoping service")
    last_seen = load_state()

    while True:
        notifications = fetch_notifications()
        newest_ts = last_seen

        for n in reversed(notifications):
            updated_at = datetime.fromisoformat(
                n["updated_at"].replace("Z", "+00:00")
            )

            if last_seen and updated_at <= last_seen:
                continue

            send_webhook(n)

            if not newest_ts or updated_at > newest_ts:
                newest_ts = updated_at

        if newest_ts and newest_ts != last_seen:
            save_state(newest_ts)
            last_seen = newest_ts

        logging.info(f"Sleeping for {POLL_INTERVAL} seconds")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
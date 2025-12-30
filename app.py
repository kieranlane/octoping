import os
import time
import json
import requests
from datetime import datetime, timezone

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
        return None
    with open(STATE_FILE, "r") as f:
        return datetime.fromisoformat(json.load(f)["last_seen"])

def save_state(ts):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_seen": ts.isoformat()}, f)

def fetch_notifications():
    r = requests.get(
        "https://api.github.com/notifications",
        headers=HEADERS,
        params={"all": "false"}
    )
    r.raise_for_status()
    return r.json()

def send_webhook(notification):
    payload = {
        "id": notification["id"],
        "reason": notification["reason"],
        "updated_at": notification["updated_at"],
        "repository": notification["repository"]["full_name"],
        "subject": notification["subject"],
        "url": notification["html_url"],
        "raw": notification,
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

def main():
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

        if newest_ts:
            save_state(newest_ts)
            last_seen = newest_ts

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
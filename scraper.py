#!/usr/bin/env python3
"""
RSA Driving Test Centre Wait Times Scraper.
Fetches estimated invitation weeks for all test centres and writes data/latest.json.
"""

import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_URL = "https://rsa.powerappsportals.com"
USER_AGENT = "RSAWaitTimes/1.0 (https://github.com/stas/rsa-wait-times; non-commercial public dashboard)"
REQUEST_DELAY = 0.5  # seconds between requests (courtesy rate limit)


def fetch_json(url, method="GET", data=None):
    headers = {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": USER_AGENT,
    }
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(url, headers=headers, method=method, data=data)
    with urlopen(req) as resp:
        return json.loads(resp.read())


def scrape():
    centres = fetch_json(f"{BASE_URL}/return-all-dtc/")
    print(f"Found {len(centres)} test centres")

    results = []
    for i, centre in enumerate(centres, 1):
        name = centre["name"]
        if i > 1:
            time.sleep(REQUEST_DELAY)
        try:
            est = fetch_json(
                f"{BASE_URL}/return-last-estimation/",
                method="POST",
                data=f"pdtcname={quote(name)}".encode(),
            )
            details = fetch_json(
                f"{BASE_URL}/_api/rsa_estimations({est['rsa_estimationid']})"
            )
            results.append(
                {
                    "name": name,
                    "invite_week": details["rsa_expectedinviteweek"][:10],
                    "weeks_wait": details["rsa_numberofweekswaitinccontingency"],
                    "queue_position": details.get("rsa_sequentialnumber"),
                }
            )
            print(f"  [{i:2d}/{len(centres)}] {name}: {results[-1]['weeks_wait']}w")
        except Exception as e:
            print(f"  [{i:2d}/{len(centres)}] {name}: ERROR - {e}")

    results.sort(key=lambda x: x["weeks_wait"])

    output = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "model_published": details.get("rsa_modelpublisheddate", "")[:10],
        "centres": results,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote data/latest.json ({len(results)} centres)")


if __name__ == "__main__":
    scrape()

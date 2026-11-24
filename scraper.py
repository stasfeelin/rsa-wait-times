#!/usr/bin/env python3
"""
RSA Driving Test Centre Wait Times Scraper.
Fetches estimated invitation weeks for all test centres and writes data/latest.json.
"""

import json
import math
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, URLError, urlopen

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


def fetch_estimation_page(estimation_id):
    query = urlencode({"lastEstimationId": estimation_id})
    req = Request(
        f"{BASE_URL}/drivertest-estimation-personal/?{query}",
        headers={
            "Accept": "text/html",
            "Referer": f"{BASE_URL}/drivertest-estimation-personal/",
            "User-Agent": USER_AGENT,
        },
    )
    with urlopen(req) as resp:
        return resp.read().decode("utf-8")


def parse_estimation_page(html):
    centre_match = re.search(
        r'\$\("#lbl-tc-testcentre"\)\.text\(("(?:\\.|[^"\\])*")\);',
        html,
    )
    invite_match = re.search(
        r'\$\("#lbl-tc-expectedinvite"\)\.text\(moment\(new Date\("([^"]+)"\)',
        html,
    )
    published_match = re.search(
        r'\$\("#lbl-tc-modelpublisheddate"\)\.text\(moment\(new Date\("([^"]+)"\)',
        html,
    )
    if not centre_match or not invite_match or not published_match:
        raise ValueError("Estimator page did not contain the expected result fields")

    centre = json.loads(centre_match.group(1).replace("\\'", "'"))
    invite_week = datetime.strptime(
        invite_match.group(1), "%m/%d/%Y %I:%M:%S %p"
    ).date()
    model_published = datetime.strptime(
        published_match.group(1), "%m/%d/%Y %I:%M:%S %p"
    ).date()
    return centre, invite_week, model_published


def scrape():
    centres = fetch_json(f"{BASE_URL}/return-all-dtc/")
    print(f"Found {len(centres)} test centres")

    results = []
    model_published = ""
    for i, centre in enumerate(centres, 1):
        name = centre["name"]
        if i > 1:
            time.sleep(REQUEST_DELAY)
        try:
            est = fetch_json(
                f"{BASE_URL}/return-last-estimation/",
                method="POST",
                data=urlencode({"pdtcname": name}).encode(),
            )
            result_centre, invite_week, published_date = parse_estimation_page(
                fetch_estimation_page(est["rsa_estimationid"])
            )
            if result_centre != name:
                raise ValueError(f"Expected {name}, got {result_centre}")

            if not model_published:
                model_published = published_date.isoformat()
            weeks_wait = max(
                0, math.ceil((invite_week - published_date).days / 7)
            )
            results.append(
                {
                    "name": name,
                    "invite_week": invite_week.isoformat(),
                    "weeks_wait": weeks_wait,
                    "queue_position": None,
                }
            )
            print(f"  [{i:2d}/{len(centres)}] {name}: {weeks_wait}w")
        except (URLError, TimeoutError, ValueError, KeyError, TypeError) as e:
            print(f"  [{i:2d}/{len(centres)}] {name}: ERROR - {e}")

    results.sort(key=lambda x: x["weeks_wait"])

    if not results:
        raise RuntimeError("No centres were scraped; data/latest.json was not updated")

    output = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "model_published": model_published,
        "centres": results,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote data/latest.json ({len(results)} centres)")


if __name__ == "__main__":
    scrape()

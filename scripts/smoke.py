"""Read-only acceptance check against a running PressLens service."""

import argparse
import csv
import io
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    def get(path):
        with urlopen(base + path, timeout=10) as response:
            assert response.status == 200
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            return response.read().decode("utf-8")

    assert json.loads(get("/health/ready"))["status"] == "ready"
    assert "PressLens" in get("/")
    options = json.loads(get("/api/v1/filters"))
    full = json.loads(get("/api/v1/dashboard"))
    assert full["meta"]["simulated"] is True
    assert full["summary"]["sessions"] == full["quality"]["accepted_rows"]
    query = urlencode({"channel": options["channels"][0], "device": options["devices"][0]})
    filtered = json.loads(get("/api/v1/dashboard?" + query))
    exported = list(csv.DictReader(io.StringIO(get("/api/v1/export.csv?" + query))))
    assert len(exported) == filtered["summary"]["sessions"]
    assert sum(int(row["subscribed"]) for row in exported) == filtered["summary"]["subscriptions"]
    assert json.loads(get("/api/v1/dashboard?category=nonexistent"))["summary"]["sessions"] == 0
    try:
        get("/api/v1/dashboard?start_date=2026-10-01&end_date=2026-08-01")
    except HTTPError as error:
        assert error.code == 422
    else:
        raise AssertionError("Reversed dates should fail")
    print(json.dumps({"status": "passed", "sessions": full["summary"]["sessions"],
                      "filtered_csv_rows": len(exported), "base_url": base}))


if __name__ == "__main__":
    main()

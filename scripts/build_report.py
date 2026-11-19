"""Build report.json from pytest JUnit XML and POST it to REPORT_URL."""
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

JUNIT = os.environ.get("JUNIT_FILE", "results/junit.xml")
OUT = "results/report.json"


def parse_tests():
    if not os.path.exists(JUNIT):
        return [{"name": "test-run", "result": "failed",
                 "failure_message": "No JUnit results found (tests did not complete)."}]
    tests = []
    for tc in ET.parse(JUNIT).getroot().iter("testcase"):
        bad = tc.find("failure")
        if bad is None:
            bad = tc.find("error")
        entry = {"name": f"{tc.get('classname')}::{tc.get('name')}",
                 "result": "failed" if bad is not None else
                 ("skipped" if tc.find("skipped") is not None else "passed")}
        if bad is not None:
            entry["failure_message"] = (bad.get("message") or bad.text or "").strip()[:1000]
        tests.append(entry)
    return tests


def build():
    tests = parse_tests()
    failed = sum(t["result"] == "failed" for t in tests)
    passed = sum(t["result"] == "passed" for t in tests)
    return {
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "branch": os.environ.get("GITHUB_REF_NAME", "local"),
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "pipeline_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": tests,
        "summary": {"total": len(tests), "passed": passed, "failed": failed},
        "overall_status": "passed" if tests and failed == 0 else "failed",
    }


def post(report, url):
    headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "1"}
    if os.environ.get("RECEIVER_TOKEN"):
        headers["X-Receiver-Token"] = os.environ["RECEIVER_TOKEN"]
    data = json.dumps(report).encode()
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=20) as r:
                print(f"Report delivered: HTTP {r.status}")
                return True
        except Exception as exc:
            print(f"Attempt {attempt} failed: {exc}")
            time.sleep(3)
    return False


if __name__ == "__main__":
    report = build()
    os.makedirs("results", exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report["summary"]), report["overall_status"])
    url = os.environ.get("REPORT_URL")
    if "--no-post" in sys.argv:
        sys.exit(0)
    if not url:
        print("REPORT_URL not set; report not delivered.")
        sys.exit(1)
    sys.exit(0 if post(report, url) else 1)

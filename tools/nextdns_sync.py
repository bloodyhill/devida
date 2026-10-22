"""Push the Hisense/VIDAA blocklist into a NextDNS profile's denylist.

Desired set = ipanalytics Blocked_Domains.txt + dns/extra-block.txt - dns/allow.txt.
Adds whatever is missing. With --prune it also removes denylist entries that
are not in the desired set (including ones you added by hand in the dashboard).

Reads NEXTDNS_API_KEY and NEXTDNS_PROFILE from the environment or from .env
in the repo root. API key: https://my.nextdns.io/account (bottom of the page).

Usage:
  python tools/nextdns_sync.py --dry-run
  python tools/nextdns_sync.py [--prune]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = "https://raw.githubusercontent.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist/main/Blocked_Domains.txt"
API = "https://api.nextdns.io"


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_domains(text):
    # Plain hostnames, one per line; '//', '#' and '!' lines are comments or disabled rules.
    domains = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("//", "#", "!")):
            continue
        line = line.removeprefix("||").removesuffix("^").split()[0].lower()
        if "." in line:
            domains.add(line)
    return domains


def read_local(name):
    path = ROOT / "dns" / name
    return parse_domains(path.read_text(encoding="utf-8")) if path.exists() else set()


def fetch_upstream():
    with urllib.request.urlopen(UPSTREAM, timeout=30) as resp:
        return parse_domains(resp.read().decode("utf-8"))


class NextDNS:
    def __init__(self, api_key, profile):
        self.api_key = api_key
        self.base = "%s/profiles/%s/denylist" % (API, urllib.parse.quote(profile))

    def _call(self, method, url, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise SystemExit("NextDNS %s %s failed: HTTP %d %s" % (method, url, e.code, detail))

    def list(self):
        return {item["id"] for item in self._call("GET", self.base).get("data", [])}

    def add(self, domain):
        self._call("POST", self.base, {"id": domain, "active": True})

    def remove(self, domain):
        self._call("DELETE", "%s/%s" % (self.base, urllib.parse.quote(domain)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the changes without making them")
    parser.add_argument("--prune", action="store_true", help="also remove denylist entries not in the desired set")
    args = parser.parse_args()

    load_env()
    desired = (fetch_upstream() | read_local("extra-block.txt")) - read_local("allow.txt")
    print("Desired denylist: %d domains" % len(desired))

    api_key, profile = os.environ.get("NEXTDNS_API_KEY"), os.environ.get("NEXTDNS_PROFILE")
    if not api_key or not profile:
        if args.dry_run:
            print("\n".join(sorted(desired)))
            print("\n(No NEXTDNS_API_KEY / NEXTDNS_PROFILE set, so this is the full list, not a diff.)")
            return
        sys.exit("Set NEXTDNS_API_KEY and NEXTDNS_PROFILE in .env (see .env.example).")

    client = NextDNS(api_key, profile)
    current = client.list()
    to_add = sorted(desired - current)
    to_remove = sorted(current - desired) if args.prune else []

    for d in to_add:
        print("+ %s" % d)
    for d in to_remove:
        print("- %s" % d)
    print("%d to add, %d to remove, %d already present" % (len(to_add), len(to_remove), len(desired & current)))

    if args.dry_run or not (to_add or to_remove):
        return
    for d in to_add:
        client.add(d)
    for d in to_remove:
        client.remove(d)
    print("Done. Denylist now has %d entries." % len(client.list()))


if __name__ == "__main__":
    main()

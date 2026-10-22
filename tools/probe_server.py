"""Serve the launcher over plain HTTP on the LAN and collect probe reports.

Open http://<this-pc>:<port>/probe.html on the TV (via the VIDAA browser or
`install_tile.py launch --url ...`), press the remote's buttons, and each
report is printed here and saved to probe-results/.

Usage: python tools/probe_server.py [--port 8000]
"""

import argparse
import json
import socket
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_DIR = ROOT / "launcher"
RESULTS_DIR = ROOT / "probe-results"
MAX_BODY = 1_000_000


def lan_ip():
    # Connecting a UDP socket sends nothing; it just picks the outbound interface.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


class ProbeHandler(SimpleHTTPRequestHandler):
    session_file = None

    def do_POST(self):
        if self.path != "/report":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self.send_error(413)
            return
        try:
            report = json.loads(self.rfile.read(length))
        except ValueError:
            self.send_error(400, "bad JSON")
            return

        # The page re-sends the full report after every key press; keep the latest.
        RESULTS_DIR.mkdir(exist_ok=True)
        self.session_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        summarize(report, self.session_file)

        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        if self.command != "POST":
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def summarize(report, path):
    device = report.get("device", {})
    keys = report.get("keys", [])
    downs = sorted({k["keyCode"] for k in keys if k.get("type") == "keydown"})
    ups = sorted({k["keyCode"] for k in keys if k.get("type") == "keyup"})
    print("\n— probe report (%s) —" % datetime.now().strftime("%H:%M:%S"))
    print("UA:        %s" % device.get("userAgent"))
    print("viewport:  %s  screen: %s" % (device.get("viewport"), device.get("screen")))
    print("TV APIs:   %s" % (", ".join(device.get("windowMatches", {})) or "none found"))
    print("keydown:   %s" % downs)
    print("keyup:     %s" % ups)
    if 13 in downs:
        print("OK keyup:  %s" % ("yes - long-press works" if 13 in ups else "NO - set okLongPress: false"))
    print("saved:     %s" % path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    ProbeHandler.session_file = RESULTS_DIR / ("probe-%s.json" % datetime.now().strftime("%Y%m%d-%H%M%S"))
    handler = partial(ProbeHandler, directory=str(LAUNCHER_DIR))
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler)
    url = "http://%s:%d/probe.html" % (lan_ip(), args.port)
    print("Serving %s" % LAUNCHER_DIR)
    print("On the TV open: %s" % url)
    print("(Windows may ask to allow Python through the firewall: allow it on private networks.)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

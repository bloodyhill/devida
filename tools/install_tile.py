#!/usr/bin/env python3
"""Pin a custom web-app tile to a Hisense VIDAA TV's home screen.

A thin CLI over the core modules of Sidee (https://github.com/Empi9245/Sidee,
MIT licence), loaded from a local clone passed with --sidee (or the
SIDEE_PATH environment variable). Discovery, PIN pairing, the MQTT session on
port 36669 and the tile payloads are all Sidee's; this script only wires them
to a generic --url/--name/--id instead of Sidee's preset catalogue.

Typical use:
  install_tile.py pair    --sidee ../Sidee
  install_tile.py install --sidee ../Sidee --id devidahome --name Home \\
                          --url https://bloodyhill.github.io/devida/
  install_tile.py apps    --sidee ../Sidee

Add --dry-run to print the MQTT topics and payloads instead of contacting
the TV.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MQTT_PORT = 36669  # same as core.client.MQTT_PORT, kept here so dry runs need no paho
SIDEE_FILES = ("client.py", "pairing.py", "protocol.py", "platform_support.py",
               "tv-client.bundle")
APP_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


class CliError(Exception):
    """A problem the user can fix; printed without a traceback."""


# --- Loading Sidee from a local clone ---

def load_sidee(path: str) -> Path:
    """Put the Sidee clone on sys.path and import its paho-free modules."""
    root = Path(path).expanduser().resolve()
    missing = [name for name in SIDEE_FILES if not (root / "core" / name).is_file()]
    if missing:
        raise CliError(f"{root} does not look like a Sidee clone "
                       f"(missing core/{', core/'.join(missing)})")
    sys.path.insert(0, str(root))
    core = importlib.import_module("core")
    # Sidee's package is called plain "core": make sure we got the clone's.
    if Path(core.__file__).resolve().parent != root / "core":
        raise CliError(f"another 'core' package shadows Sidee's: {core.__file__}")
    return root


def sidee_module(name: str):
    return importlib.import_module(f"core.{name}")


def sidee_client(root: Path):
    """core.client needs paho-mqtt; import it only when talking to the TV."""
    try:
        return sidee_module("client")
    except ModuleNotFoundError as e:
        if (e.name or "").split(".")[0] == "paho":
            raise CliError("Sidee needs paho-mqtt. Install it with:\n"
                           f"  python -m pip install -r \"{root / 'requirements.txt'}\""
                           ) from e
        raise


def load_session(client, ip: str | None):
    try:
        session = client.Session.load()
    except FileNotFoundError:
        raise CliError("no paired TV found: run the 'pair' subcommand first") from None
    except (client.AuthError, ValueError, TypeError, KeyError) as e:
        raise CliError(f"the saved Sidee session is unusable ({e}): "
                       "run 'pair' again") from None
    if ip:
        session.host = ip  # TV got a new address on the hotspot
    return session


# --- Dry runs ---

def saved_identity() -> dict | None:
    """Read session.json the way Sidee stores it, without importing paho."""
    platform_support = sidee_module("platform_support")
    protocol = sidee_module("protocol")
    path = platform_support.profile_dir() / "session.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data.get("device_uuid"):
        return None
    client_id = data.get("client_id") or protocol.session_credentials(
        data["device_uuid"], 0, auth_profile=data.get("auth_profile", "modern"),
        brand=data.get("brand", "his"))[0]
    return {"path": path, "host": data.get("host", ""), "client_id": client_id,
            "device_uuid": data["device_uuid"],
            "auth_profile": data.get("auth_profile", "modern")}


def dry_run_header(ip: str | None, identity: dict | None) -> dict:
    protocol = sidee_module("protocol")
    if identity:
        print(f"[dry-run] session: {identity['path']} "
              f"(auth profile {identity['auth_profile']})")
        client_id = identity["client_id"]
    else:
        print("[dry-run] no saved session: run 'pair' first; "
              "topics below use a placeholder client id")
        client_id = "<client_id>"
    host = ip or (identity or {}).get("host") or "<tv-ip>"
    bundle = Path(protocol.__file__).resolve().parent / "tv-client.bundle"
    print(f"[dry-run] broker: mqtts://{host}:{MQTT_PORT}  (client cert {bundle})")
    return protocol.tv_topics(client_id)


def show(action: str, topic: str, payload: str | None = None) -> None:
    print(f"[dry-run] {action} {topic}")
    if payload is not None:
        print(f"          payload: {payload if payload else '(empty)'}")


# --- Subcommands ---

def pick_tv(client) -> str:
    print("Searching for VIDAA TVs on the network (about 5 s)...")
    tvs = client.discover()
    if not tvs:
        raise CliError("no VIDAA TV answered discovery. Phone hotspots often "
                       "block SSDP broadcasts: pass the TV's address with --ip "
                       "(Settings > Network > Network information on the TV)")
    if len(tvs) == 1:
        print(f"Found {tvs[0].friendly_name} at {tvs[0].host}")
        return tvs[0].host
    for i, tv in enumerate(tvs, 1):
        print(f"  {i}. {tv.host}  {tv.friendly_name}")
    while True:
        choice = input(f"Which TV? [1-{len(tvs)}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(tvs):
            return tvs[int(choice) - 1].host


def ask_pin() -> str:
    while True:
        pin = input("4-digit PIN shown on the TV: ").strip()
        if re.fullmatch(r"[0-9]{4}", pin):
            return pin
        print("The PIN is exactly 4 digits.")


def cmd_pair(a, root: Path) -> int:
    if a.dry_run:
        protocol = sidee_module("protocol")
        identity = saved_identity()
        host = a.ip or "<discovered-tv-ip>"
        reuse = identity and identity["host"] == a.ip
        device_uuid = identity["device_uuid"] if reuse else protocol.new_device_uuid()
        # The brand comes from the TV's UPnP descriptor; "his" on Hisense.
        client_id = protocol.session_credentials(device_uuid, 0, brand="his")[0]
        topics = protocol.tv_topics(client_id)
        print(f"[dry-run] would pair with {host} as device {device_uuid} "
              f"({'reused' if reuse else 'new'} identity)")
        print(f"[dry-run] broker: mqtts://{host}:{MQTT_PORT}")
        show("SUBSCRIBE", topics["mobile"] + "ui_service/data/authentication")
        show("SUBSCRIBE", topics["mobile"] + "ui_service/data/authenticationcode")
        show("SUBSCRIBE", topics["token_reply"])
        show("PUBLISH", topics["ui"] + "actions/vidaa_app_connect",
             protocol.pair_connect_payload())
        show("PUBLISH", topics["ui"] + "actions/authenticationcode",
             protocol.pair_pin_payload("1234"))
        show("PUBLISH", topics["platform"] + "data/gettoken",
             protocol.token_request_payload(""))
        print("[dry-run] (static-auth firmware first sends actions/gettvstate; "
              "Sidee picks the profile at connect time)")
        return 0
    client = sidee_client(root)
    host = a.ip or pick_tv(client)
    print(f"Connecting to {host}; a PIN should appear on the TV within ~15 s...")
    session = client.pair(host, ask_pin)
    print(f"Paired with {session.host} (auth profile: {session.auth_profile}).")
    print(f"Session saved to {client.Session.path()}")
    return 0


def cmd_install(a, root: Path) -> int:
    if a.dry_run:
        protocol = sidee_module("protocol")
        topics = dry_run_header(a.ip, saved_identity())
        # Same sequence as core.client.add_tile.
        show("SUBSCRIBE", topics["applist_reply"])
        show("PUBLISH", topics["ui"] + "actions/uievent",
             protocol.install_payload(a.id, a.name, a.url, a.icon or ""))
        show("PUBLISH", topics["ui"] + "actions/applist", "0")
        print("[dry-run] then checks the app list for "
              f"appId={a.id} with url={a.url}")
        return 0
    client = sidee_client(root)
    session = load_session(client, a.ip)
    print(f"Installing '{a.name}' on {session.host} (takes ~15 s)...")
    apps = client.add_tile(session, a.id, a.name, a.url, a.icon or "")
    if any(client.tile_matches_request(x, a.id, a.url) for x in apps):
        print(f"REGISTERED: {a.name} ({a.id}) -> {a.url}")
        return 0
    print(f"NOT confirmed by the TV: {a.name} ({a.id}) -> {a.url}\n"
          "Check the home screen anyway; some firmwares register the tile "
          "without listing it. Run 'apps' to see what the TV reports.")
    return 1


def cmd_launch(a, root: Path) -> int:
    if a.dry_run:
        protocol = sidee_module("protocol")
        topics = dry_run_header(a.ip, saved_identity())
        show("PUBLISH", topics["ui"] + "actions/launchapp",
             protocol.launch_payload(a.id, a.name, a.url))
        return 0
    client = sidee_client(root)
    session = load_session(client, a.ip)
    client.launch_tile(session, a.id, a.name, a.url)
    print(f"Launch request sent to {session.host}.")
    return 0


def cmd_apps(a, root: Path) -> int:
    if a.dry_run:
        topics = dry_run_header(a.ip, saved_identity())
        show("SUBSCRIBE", topics["applist_reply"])
        show("PUBLISH", topics["ui"] + "actions/applist", "0")
        return 0
    client = sidee_client(root)
    apps = client.list_tiles(load_session(client, a.ip))
    if a.json:
        print(json.dumps(apps, indent=2, ensure_ascii=False))
        return 0
    if not apps:
        print("The TV sent no app list (or an empty one).")
        return 1
    apps = [app for app in apps if isinstance(app, dict)]
    for app in apps:
        url = app.get("url") or app.get("appUrl") or app.get("URL") or ""
        print(f"  {str(app.get('appId', '?')):<24} {str(app.get('name', '')):<24} "
              f"{str(url)[:70]}")
    print(f"{len(apps)} apps")
    return 0


# --- Argument parsing ---

def web_url(value: str) -> str:
    u = urlsplit(value)
    if u.scheme not in ("http", "https") or not u.netloc:
        raise argparse.ArgumentTypeError(f"not an http(s) URL: {value!r}")
    return value


def app_id(value: str) -> str:
    if not APP_ID.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "use 1-64 letters, digits, '.', '_' or '-' (e.g. devidahome)")
    return value


def tile_name(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("the tile name cannot be empty")
    return value.strip()


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--sidee", metavar="PATH", default=os.environ.get("SIDEE_PATH"),
                        help="path to a local clone of github.com/Empi9245/Sidee "
                             "(default: $SIDEE_PATH)")
    common.add_argument("--ip", metavar="ADDR",
                        help="TV address; skips discovery for 'pair' and overrides "
                             "the saved address for the other commands")
    common.add_argument("--dry-run", action="store_true",
                        help="print the MQTT topics and payloads instead of sending")

    tile = argparse.ArgumentParser(add_help=False)
    tile.add_argument("--url", required=True, type=web_url,
                      help="HTTPS address of the web app the tile opens")
    tile.add_argument("--name", required=True, type=tile_name,
                      help="label shown under the tile")
    tile.add_argument("--id", required=True, type=app_id,
                      help="stable app id; reuse it to replace an existing tile")

    p = argparse.ArgumentParser(
        prog="install_tile.py",
        description="Pin a custom web-app tile to a Hisense VIDAA TV's home "
                    "screen using Sidee's core modules.",
        epilog="Run '<command> --help' for each command's options.")
    sub = p.add_subparsers(dest="cmd", metavar="command")
    sub.required = True

    pr = sub.add_parser("pair", parents=[common],
                        help="pair with the TV using the PIN it displays",
                        description="Find the TV (or use --ip), ask it to show a "
                                    "PIN, and save the session to Sidee's "
                                    "~/.sidee/session.json.")
    pr.set_defaults(func=cmd_pair)

    ins = sub.add_parser("install", parents=[common, tile],
                         help="pin a web app to the home screen",
                         description="Send Sidee's app_install payload "
                                     "(StoreType 99) and confirm the tile appears "
                                     "in the TV's app list.")
    # No string default: argparse would run web_url on it.
    ins.add_argument("--icon", metavar="URL", type=web_url,
                     help="square tile image URL (optional)")
    ins.set_defaults(func=cmd_install)

    la = sub.add_parser("launch", parents=[common, tile],
                        help="open a web app on the TV now",
                        description="Send Sidee's launchapp payload.")
    la.set_defaults(func=cmd_launch)

    ap = sub.add_parser("apps", parents=[common],
                        help="list the apps installed on the TV",
                        description="Ask the TV for its app list.")
    ap.add_argument("--json", action="store_true", help="print the raw app list")
    ap.set_defaults(func=cmd_apps)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    a = parser.parse_args(argv)
    if not a.sidee:
        parser.error("--sidee PATH (or SIDEE_PATH) is required: "
                     "git clone https://github.com/Empi9245/Sidee")
    try:
        root = load_sidee(a.sidee)
        return a.func(a, root)
    except KeyboardInterrupt:
        print("\ncancelled", file=sys.stderr)
        return 130
    except Exception as e:  # report TV/session problems without a traceback
        client = sys.modules.get("core.client")
        known = (CliError, OSError, ValueError, EOFError)
        if client is not None:
            known += (client.AuthError, client.PairingCancelled)
        if not isinstance(e, known):
            raise
        print(f"error: {e}", file=sys.stderr)
        if client is not None and isinstance(e, client.AuthError):
            print("hint: run 'pair' again", file=sys.stderr)
        elif isinstance(e, OSError):
            print(f"hint: check the TV is on, on the same network as this PC, "
                  f"and reachable on port {MQTT_PORT} (pass --ip if its "
                  "address changed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

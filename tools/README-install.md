# install_tile.py — pin the launcher to the VIDAA home screen

> Optional: only needed if you use VIDAA's own apps. With the Apple TV setup ([../docs/APPLE-TV.md](../docs/APPLE-TV.md)) the TV stays offline and has no use for a tile.

VIDAA has no ADB and you can't replace its home screen, but its local
control interface (MQTT over TLS on port 36669, the channel the official
VIDAA phone app uses) accepts an `app_install` request. That request adds a
web-app tile to the home row. `install_tile.py` uses it to pin the devida
launcher (or any HTTPS web app) as a tile.

## Credit: Sidee

This tool is a thin CLI over **[Sidee](https://github.com/Empi9245/Sidee)**
by Empi9245 (MIT licence). TV discovery, PIN pairing, session and token
handling, the TV client certificate (`core/tv-client.bundle`) and the
`install_payload` / `launch_payload` messages all come from Sidee's `core/`
modules. None of Sidee's code is copied here. The script imports it at
runtime from a clone you provide with `--sidee`. Sidee's licence and
copyright stay with that clone.

## Setup

Python 3.9 or newer.

```bash
git clone https://github.com/Empi9245/Sidee
```

```bash
python -m pip install -r Sidee/requirements.txt
```

The second command installs `paho-mqtt`, which only commands that talk to
the TV need. `--help` and `--dry-run` work without it.

Pass the clone with `--sidee PATH` on every command, or set it once with the
`SIDEE_PATH` environment variable (PowerShell: `$env:SIDEE_PATH = "C:\path\to\Sidee"`).

The PC and the TV must be on the same network: here, the phone hotspot.

## Usage

### 1. Pair (once)

```bash
python tools/install_tile.py pair --sidee ../Sidee
```

The script searches the network for the TV. If it finds none (phone
hotspots often drop the SSDP broadcasts discovery relies on), give the
address directly. You can find it on the TV under Settings > Network >
Network information:

```bash
python tools/install_tile.py pair --sidee ../Sidee --ip 172.20.10.3
```

A 4-digit PIN appears on the TV. Type it at the prompt within about a
minute. Sidee saves the session (device identity and tokens) to
`~/.sidee/session.json` (`%USERPROFILE%\.sidee\session.json` on Windows).
The later commands reuse that session, and Sidee refreshes the tokens on
its own. Pair again only if the TV forgets the device.

### 2. Install the tile

```bash
python tools/install_tile.py install --sidee ../Sidee --id devidahome --name Home --url https://bloodyhill.github.io/devida/
```

| Option | Meaning |
| --- | --- |
| `--url` | HTTPS address of the web app the tile opens. |
| `--name` | Label shown under the tile. |
| `--id` | Stable app id (letters, digits, `.`, `_`, `-`). Installing again with the same id replaces the tile instead of adding a duplicate. |
| `--icon` | Optional square image URL for the tile. |

This sends Sidee's `app_install` payload (`StoreType 99`), waits about
15 seconds, and then asks the TV for its app list to confirm that a tile with
that id and URL exists. It prints `REGISTERED` on success. It prints
`NOT confirmed by the TV` and exits 1 if the list doesn't show the tile.
Some firmware registers the tile without listing it, so check the home
screen too.

### 3. Launch it now (optional)

```bash
python tools/install_tile.py launch --sidee ../Sidee --id devidahome --name Home --url https://bloodyhill.github.io/devida/
```

### 4. List installed apps

```bash
python tools/install_tile.py apps --sidee ../Sidee
```

Add `--json` to print the TV's raw reply.

### Options on every command

- `--ip ADDR`: for `pair`, skips discovery. For the other commands, it
  overrides the address saved at pairing time. Use it when the hotspot hands
  the TV a new IP.
- `--dry-run`: prints the MQTT broker, topics and exact payloads instead of
  connecting. With a saved session it shows your real client id. Without one
  it shows a placeholder. Use it to check a URL or id before touching the TV:

```bash
python tools/install_tile.py install --sidee ../Sidee --dry-run --id devidahome --name Home --url https://bloodyhill.github.io/devida/
```

## Firmware caveat

Sidee is tested mainly on firmware **U09.60 (V0000.09.60A.Q0707)**. This TV
runs a **V0000.09.09** build of the same VIDAA U9 generation. The protocol is
very likely the same, but that hasn't been verified on this firmware.
Possible differences:

- Pairing tries Sidee's four authentication profiles (`static`, `modern`,
  `middle`, `remotenow`) in turn. If the TV rejects all of them, the error
  includes the TV's public model details. Sidee's
  [compatibility notes](https://github.com/Empi9245/Sidee/blob/main/docs/toshiba-compatibility.md)
  cover what is known.
- The tile may install but be missing from the app list
  (`NOT confirmed by the TV`). Check the home screen before retrying.
- A firmware update may remove custom tiles. Run `install` again; the same
  `--id` keeps it a single tile.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `no VIDAA TV answered discovery` | Use `--ip`. Check the TV is on and joined to the hotspot. |
| `Sidee needs paho-mqtt` | `python -m pip install -r <Sidee>/requirements.txt` |
| `connection ... refused` / timeouts | Check the TV is on, on the same network, and the IP is current (`--ip`). Some hotspots isolate clients from each other: turn that off if the phone offers it. |
| `no paired TV found` / `session is unusable` / `run 'pair' again` | Run `pair` again. |
| `the TV did not display the PIN` | Wake the TV (not standby) and retry `pair`. |

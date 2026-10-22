# devida

Cleaning up a Hisense VIDAA TV: no ads, no viewing-data collection, and a calm Apple TV-style experience.

## Recommended: Hisense + Apple TV

Follow **[docs/APPLE-TV.md](docs/APPLE-TV.md)**.

- The Apple TV is the interface, and the Hisense is just a screen.
- HDMI-CEC wakes, switches and sleeps the TV with the Apple TV.
- AirPlay comes from the Apple TV.
- The TV stays **offline**, so VIDAA has no ads to show and nowhere to send data.

Before taking the TV offline, withdraw its data consents with [docs/TV-SETTINGS.md](docs/TV-SETTINGS.md).

That's the whole setup. Everything below is optional.

## What VIDAA does and doesn't allow

- **No deep changes.** VIDAA has no ADB, no way to replace the system home screen, and signature-checked firmware updates. So the tricks [dumbtv](https://github.com/humblemuzzu/dumbtv) uses on Fire TV don't work here.
- **Web pages can't drive the TV.** A device probe on this TV (50A51HXVT, VIDAA U09.09) found 195 TV-specific functions available to web pages. None of them switches HDMI inputs, launches built-in apps or starts AirPlay. Details are in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Optional: if you use VIDAA's own apps

Only needed if the TV stays online, for example to use VIDAA apps without the Apple TV. Nothing is installed into the TV's system, and every step can be undone.

| Piece | What it does | Limit |
| --- | --- | --- |
| **DNS blocking** (`tools/nextdns_sync.py`, `dns/`) | A NextDNS profile with the [VIDAA blocklist](https://github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist) (137 hosts) + HaGeZi blocks ads, recommendations and telemetry | YouTube ads can't be blocked by DNS; the app store may partly break |
| **Launcher** (`launcher/`, live at https://bloodyhill.github.io/devida/) | A tvOS-style home for web apps (YouTube TV, Stremio, Nuvio, Jellyfin) | The stock home still appears at power-on; built-in apps (Netflix…) open from there |
| **Tile installer** (`tools/install_tile.py`) | Pins the launcher to the VIDAA home using [Sidee](https://github.com/Empi9245/Sidee)'s pairing | Not yet tested on this firmware; see [tools/README-install.md](tools/README-install.md) |
| **Device probe** (`launcher/probe.html`, `tools/probe_server.py`) | Lists what a web page can do on the TV | Already run; results in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

### DNS blocking

1. **Set up NextDNS.**
   - Create a free account at [nextdns.io](https://nextdns.io).
   - In **Privacy**, add the *HaGeZi – Multi PRO* blocklist and turn on *Native Tracking Protection*.
   - In **Setup → Linked IP**, link your IP from the PC while it's on the phone hotspot, and copy the update URL.
2. **Push the VIDAA blocklist.** Copy `.env.example` to `.env`, fill in the API key and profile ID, then run:
   ```bash
   python tools/nextdns_sync.py --dry-run
   ```
   ```bash
   python tools/nextdns_sync.py
   ```
3. **Point the TV at NextDNS:** Manual DNS, as described in [docs/TV-SETTINGS.md](docs/TV-SETTINGS.md#dns-only-for-the-nextdns-setup).

### Launcher

1. In `launcher/config.js`, paste the NextDNS update URL into `nextdnsLinkUrl`; opening the launcher then re-links the hotspot's changing IP. Add `jellyfinUrl` if you run Jellyfin.
2. Push to `main`. GitHub Pages redeploys `launcher/` automatically.
3. Pin it to the VIDAA home with `tools/install_tile.py` (see [tools/README-install.md](tools/README-install.md)).

The repo is public, so anything in `config.js` is too. Someone with the NextDNS link URL could re-point your profile's linked IP.

| Remote | Action |
| --- | --- |
| Arrows | Move focus |
| OK | Open app |
| Hold OK / Red | Move or hide the app |
| Settings tile | Show hidden apps, reset layout, run the probe |

To add an app, add an entry to `launcher/apps.json`:
- `type: "web"` with an HTTPS `url`
- a `glyph` (`play`, `stremio`, `jellyfin`, `letter`, `wordmark`, `gear`) or an `icon` URL
- two `colors` for the tile gradient

Preview on a computer:
```bash
python -m http.server 8090 --directory launcher
```
Then open http://localhost:8090. The arrow keys and Enter act as the remote, and M stands in for the red key.

## Undo

- **Apple TV setup:** reconnect the TV to Wi-Fi, and turn CEC off if you don't want it.
- **DNS:** set the TV's IP Settings back to **Auto**.
- **Launcher:** remove the tile from the VIDAA app list.
- **Consents:** re-enable any you want back.

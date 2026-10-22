# devida

A cleaner Hisense VIDAA TV: ads and telemetry blocked at the DNS level, privacy settings tightened, and an Apple TV-style home you open as a tile.

## What VIDAA does and doesn't allow

VIDAA has no ADB and no way to replace the system home screen, and firmware updates are signature-checked. So the tricks [dumbtv](https://github.com/humblemuzzu/dumbtv) uses on Fire TV don't work here. What this project does instead:

| Goal | How | Limit |
| --- | --- | --- |
| Block ads, recommendations and telemetry | NextDNS profile with the [VIDAA blocklist](https://github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist) (137 hosts) + HaGeZi | YouTube ads can't be blocked by DNS; the app store may partly break |
| Stop the TV collecting viewing data | Withdraw consents on the TV ([docs/TV-SETTINGS.md](docs/TV-SETTINGS.md)) | Done by hand, once |
| Clean tvOS-style home | `launcher/` web app, pinned to the VIDAA home as a tile | The stock home still appears at power-on; built-in apps (Netflix…) open from there |

Nothing is installed into the TV's system, and every step can be undone.

## Setup

1. **NextDNS profile.**
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
3. **TV DNS and privacy.** Follow [docs/TV-SETTINGS.md](docs/TV-SETTINGS.md).
4. **Launcher config.** In `launcher/config.js`, paste the NextDNS update URL into `nextdnsLinkUrl`. Opening the launcher then re-links the hotspot's changing IP. Add `jellyfinUrl` if you run Jellyfin.
5. **Host the launcher** on any HTTPS static host (GitHub Pages works) and note its URL.
6. **Pin it to the VIDAA home** with `tools/install_tile.py`. It uses [Sidee](https://github.com/Empi9245/Sidee)'s pairing; see `tools/README-install.md`.
7. **Probe the TV once**:
   ```bash
   python tools/probe_server.py
   ```
   Then open the printed URL on the TV and record the results in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Using the launcher

| Remote | Action |
| --- | --- |
| Arrows | Move focus |
| OK | Open app |
| Hold OK / Red | Move or hide the app |
| Settings tile | Show hidden apps, reset layout, run the probe |

To add an app, add an entry to `launcher/apps.json`: `type: "web"` with an HTTPS `url`, a `glyph` (`play`, `stremio`, `jellyfin`, `letter`, `wordmark`, `gear`) or an `icon` URL, and two `colors` for the tile gradient.

Preview on a computer:
```bash
python -m http.server 8090 --directory launcher
```
Then open http://localhost:8090. The arrow keys and Enter act as the remote, and M stands in for the red key.

## Undo

- Set the TV's IP Settings back to **Auto**.
- Remove the tile from the VIDAA app list.
- Re-enable any consents you want back.

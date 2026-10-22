# Troubleshooting

## Device facts (fill in after running the probe)

Run `python tools/probe_server.py`, open the printed URL on the TV, and press every remote button. Then record what it found:

| Fact | Value on this TV |
| --- | --- |
| Firmware | V0000.09.09… (from Settings → Support → System Info) |
| Browser user agent | _probe_ |
| Viewport | _probe_ |
| Back key code | _probe_ (launcher assumes 8; also accepts 461 / 10009) |
| Colour key codes | _probe_ (launcher assumes red = 403) |
| OK sends keyup? | _probe_. If **no**, set `okLongPress: false` in `launcher/config.js` |
| TV APIs visible to web apps | _probe_ (`windowMatches`). Any app-launch function here can power `launchNative` |

## DNS

**Ads or tracking still show up.**
- Open NextDNS → Logs and filter by the TV. If no TV queries appear, the TV isn't using NextDNS: check the Manual DNS values.
- If queries appear but nothing is blocked, the linked IP is stale. Open the launcher (it re-links) or visit the link URL from the PC on the hotspot.
- If the home screen is still busy, look in Logs for `hismarttv.com` / `vidaa` hosts that weren't blocked. Add them to `dns/extra-block.txt` and re-run `nextdns_sync.py`.

**An app or the app store broke.**
- Find the blocked hostname in NextDNS → Logs at the moment it fails.
- Add it to `dns/allow.txt`, then run `python tools/nextdns_sync.py --prune`.
- The upstream list knowingly blocks parts of the app store.

**YouTube still shows ads.** Expected. YouTube serves ads from the same hosts as videos, so DNS can't separate them.

**No internet after the hotspot restarted.** The hotspot subnet probably changed. See the hotspot note in [TV-SETTINGS.md](TV-SETTINGS.md).

**Quick check that filtering is live.** In the TV's browser, or on the PC on the same hotspot, open `https://test.nextdns.io`. It should report `"status": "ok"` and your profile.

## Launcher

**Tile opens a blank page.** The URL has to be HTTPS and publicly reachable (GitHub Pages). An `http://` LAN address only works for the probe server.

**Probe results don't reach the PC.**
- The PC and TV must be on the same hotspot.
- Windows Firewall must allow Python on private networks.
- Some phones isolate hotspot clients from each other. If yours does, read the results off the TV screen instead.

**Back doesn't return from a web app.** That's up to the app. Long-press Home (or press Home) to get back to VIDAA, then open the tile again.

**Netflix / Prime tiles are missing.** That's on purpose: `showNative` stays `false` until the probe finds a way for a web page to launch built-in apps. Without one, those apps are opened from the VIDAA home.

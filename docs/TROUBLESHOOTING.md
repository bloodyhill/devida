# Troubleshooting

## Device facts (fill in after running the probe)

Run `python tools/probe_server.py`, open the printed URL on the TV, and press every remote button. Then record what it found:

| Fact | Value on this TV |
| --- | --- |
| Model / chip | VIDAA-MT9602, VIDAA 9.0, firmware V0000.09.09Q P1015 |
| Browser | Chromium 111 (Hisense "Odin" browser); modern JS and CSS are fine |
| Viewport | 1920×1080, devicePixelRatio 1 |
| Arrows / OK / digits | 37–40 / 13 / 48–57 |
| OK sends keyup? | Yes, with repeats while held, so hold-OK works |
| Back, Input, Home, Settings | Handled by VIDAA before the page sees them: the launcher can't capture or override these keys |
| Colour key codes | _not yet probed_ (launcher assumes red = 403) |
| Model | 50A51HXVT, VIDAA U09.09, region EM_A, country SAU, 4K panel (web apps render at 720p), HDR10/HLG/Dolby Vision |
| Privacy flags | `adTargetEnable` 0, `eulaAdEnable` 0: ad targeting already off |
| Casting (DIAL) | Enabled for YouTube, YouTube TV, YouTube Kids, Netflix, Amazon, iPlayer: the phone cast button works for these |
| TV APIs visible to web apps | ~60 read-only `Hisense_Get*` getters; `Hisense_RegisterObserver` / `UnregisterObserver`, `Hisense_SetRemoteKeyboard`, `Hisense_LoginWithVIDAA`, `Hisense_enableVKB` / `disableVKB`; `TvInfo_getParam` / `setParam` / `getCurrentParam` / `setParamObserver`; `omi_platform` and `opera_omi` (`addPlatformEventListener`, `sendPlatformMessage`); `oipfObjectFactory` (HbbTV: application manager, video broadcast, channel config…) |
| Input switching / app launch / AirPlay | **None.** Confirmed over the full list of 195 functions (see the conclusion below) |

What's known about these APIs:
- **`omi_platform.sendPlatformMessage`** is real, but the only message type people have seen it act on is a launcher refresh (`AllAppsUpdate`). Nobody has documented an input-switch or app-launch message yet ([NoobyGains/stremio-vidaa-tv](https://github.com/NoobyGains/stremio-vidaa-tv) notes the TV ignores its play messages).
- **OIPF / HbbTV objects** cover broadcast channels and web apps opened by URL. The standard defines no HDMI input switching.
- **`Hisense_installApp`** only works from whitelisted store origins, not from github.io.
- **`TvInfo_*`** wraps a fixed list of settings. [anax/omavidaa](https://github.com/anax/omavidaa) reverse-engineered the same chip and firmware family and lists about 60 parameter names (volume, mute, picture mode, ad flags, kids/store/hotel mode…). None of them is an input source. The same project probed the TV's local services (`appmgr`, `app`, `system`, `launcher`, `tvmgr`) and found none.
- **`getTVProprietaryFunctions()`** (HbbTV vendor extensions) returns `null` on this TV, so there are none.
- **`vowOS`** (also visible to github.io pages, 195 functions in all):
  - `vowOS.tvinfo`: brightness, contrast, kids mode, art mode, store/hotel mode, version info.
  - `vowOS.store`: `getInstalledPkgs`, `installApp`, `sendPkgmgrRequest`.
  - `vowOS.service`: a socket and `syncExecute` bridge to the TV's local `tvinfo` / `hiutils` / `pkgmgr` services.

  None of these switches inputs or launches apps.

**Conclusion (probe of 2026-10-23):** a web page on this firmware can read TV state and change a few picture and parental settings, but it can't switch HDMI inputs, open built-in apps or start AirPlay. Use HDMI-CEC with an external box instead ([APPLE-TV.md](APPLE-TV.md)).

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

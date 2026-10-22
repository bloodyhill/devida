# Hisense + Apple TV

The Apple TV is the whole interface. The Hisense just becomes a screen: it wakes, switches input and sleeps along with the Apple TV, and VIDAA has nothing to show and nowhere to send data.

Hisense menu names move between VIDAA builds, so each step gives the **expected** path. If something isn't there, look under Settings → System, Settings → Connection or the Inputs menu.

## 1. Cable

- Connect the Apple TV to the HDMI port you'll set to *Enhanced* in step 2.
- If you add a soundbar later, keep the port marked **ARC/eARC** free for it.
- Use a High Speed or Ultra High Speed HDMI cable. 4K HDR needs one.

## 2. Hisense: HDMI-CEC

CEC is what lets the two devices control each other over the HDMI cable.

Settings → System → **HDMI & CEC** (sometimes Settings → Connection, or Inputs → HDMI control):

| Setting | Value | What it does |
| --- | --- | --- |
| CEC Function | **On** | Turns CEC on |
| TV Auto Power On | **On** | Waking the Apple TV turns the TV on and switches to its input |
| Device Auto Power Off | **On** | Turning the TV off puts the Apple TV to sleep |
| HDMI Format (for the Apple TV's port) | **Enhanced** | Allows 4K60 HDR and Dolby Vision. On *Standard*, HDR looks washed out or is missing |

## 3. Apple TV

- **Settings → Remotes and Devices**
  - Control TVs and Receivers: **On**
  - Volume Control: **Auto**. If the Apple remote's volume does nothing, choose *Learn New Device* and teach it the Hisense remote's volume keys.
- **Settings → Video and Audio**
  - Format: **4K SDR 60 Hz**
  - Match Content → Match Dynamic Range: **On**, and Match Frame Rate: **On**

  This keeps the menus in clean SDR and switches automatically to HDR10, HLG or Dolby Vision (your panel supports all three) when a film needs it.
- **Settings → Video and Audio → Check HDMI Connection:** optional; it tests the cable.
- **Settings → Privacy & Security**
  - Tracking: **don't allow apps to ask**
  - Analytics & Improvements: **off**

## 4. Power-on input

With CEC, pressing the Apple TV remote wakes everything and lands on the Apple TV. To make the **Hisense** remote's power button land there too, set the TV to start on its last input instead of the VIDAA home:

- Settings → System → Advanced Settings → **Power On Input** / **Startup** → *Last input*, or
- Settings → System → Power & Energy → **Power on behavior** → *Last input*

Some VIDAA builds only show this option in **Home Mode** (Settings → System → Advanced Settings → Usage Mode). If your build has no such option, use the Apple TV remote for power. It controls power, volume and the input switch, so the Hisense remote can go in a drawer.

## 5. Keep VIDAA quiet: take the TV offline

The Apple TV does all the streaming, so the TV no longer needs the internet. Taking it offline is the strongest debloat there is: no ads, no viewing-data (ACR) uploads, no VIDAA Free, no telemetry. It also stops VIDAA using your iPhone hotspot's mobile data in the background.

1. First do the consent checklist in [TV-SETTINGS.md](TV-SETTINGS.md), so everything is already off if you ever reconnect.
2. Settings → Network → **Wake on Wireless Network / Wake on LAN: Off**.
3. Settings → Network → Network Configuration → select the iPhone hotspot → **Forget**. Turn Wi-Fi off if the menu offers it.
4. Settings → System → Time → set the clock **manually** if the TV's clock matters to you; it can't fetch the time offline.

CEC, HDMI, picture settings and the TV's speakers all work offline.

**What you give up:**
- VIDAA's own apps. The Apple TV replaces them.
- Firmware updates. Once or twice a year, reconnect the TV, run Settings → Support → System Update, then forget the network again.

If you'd rather keep VIDAA online, for example for its apps, use the NextDNS setup in the [README](../README.md) instead. It blocks the ad and telemetry hosts but keeps the TV connected.

## 6. Picture (Apple TV input only)

Hisense saves picture settings per input. With the Apple TV showing, open the picture menu:

- **Picture Mode:** Theater / Filmmaker / Movie for films, Standard for everyday. Dolby Vision content switches to its own Dolby Vision modes automatically.
- **Motion smoothing** (Motion Enhancement / Smooth Motion / MEMC): **Off**. It causes the "soap opera" look.
- **Noise Reduction:** **Off**. Apple TV streams are already clean.

## 7. AirPlay

AirPlay comes from the Apple TV, not the Hisense. With *TV Auto Power On* enabled, AirPlaying from your iPhone wakes the Apple TV, which turns the TV on and switches to it.

If the iPhone sharing to the Apple TV is also the hotspot it's connected to, the Apple TV may not appear in the AirPlay list. Apple TV 4K also supports peer-to-peer AirPlay with no shared network; if it still doesn't appear, check Settings → AirPlay and HomeKit → Allow Access.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| TV turns on by itself | Something woke the Apple TV (AirPlay, a HomePod, the remote being bumped). Narrow **AirPlay → Allow Access** to *Only People Sharing This Home*, or turn **TV Auto Power On** off |
| TV turns on but stays on VIDAA | Set the power-on input (step 4). Then turn **CEC Function** off and on, and unplug both devices for 30 seconds |
| Apple remote volume doesn't work | Apple TV → Remotes and Devices → Volume Control → *Learn New Device* |
| HDR or Dolby Vision looks dull, or isn't offered | Set the port's **HDMI Format** to *Enhanced*, then run *Check HDMI Connection* on the Apple TV |
| Black screen flashes when a film starts | Normal: Match Content is switching modes. Turn Match Frame Rate off if it bothers you |

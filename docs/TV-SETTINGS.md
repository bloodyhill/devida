# TV privacy settings (VIDAA)

Do this on the remote once. Menu names move around between VIDAA builds, so each item gives the **expected** path; if it's elsewhere on your TV, search the Settings menu and fix the path here.

Leave the main **VIDAA / Smart TV terms of service** accepted. Declining them turns off every app, YouTube and Netflix included. Everything below is an optional consent or feature.

## Consents to withdraw

| Setting | Expected path | Set to |
| --- | --- | --- |
| Viewing Information Services (ACR: screen-content recognition) | Settings → Support → Disclaimer & Privacy | Off / withdraw |
| Interest-based / personalised ads | Settings → Support → Disclaimer & Privacy | Off |
| Voice recognition / voice data | Settings → Support → Disclaimer & Privacy | Off (voice search stops working) |
| Usage data / product improvement | Settings → Support → Disclaimer & Privacy | Off |
| Advertising ID | Settings → Support → Disclaimer & Privacy (or System → Advanced) | Reset, then limit ad tracking if offered |

## Features to turn off

| Setting | Expected path | Set to |
| --- | --- | --- |
| Auto firmware upgrade | Settings → Support → System Update | Off (check for updates by hand now and then) |
| Notifications / pop-ups | Settings → System → Notifications | Off |
| VIDAA Free channels on the home and channel list | Settings → Channel → VIDAA Free (or the channel list) | Off or remove |
| Start-up screen | Settings → System → Advanced Settings → Power On Mode / Start-up | Last input rather than Home (if offered) |
| Store / demo mode | Settings → System → Advanced Settings → Usage Mode | Home Mode |
| Wake on LAN / Wake on wireless network | Settings → Network | Off |
| Screen sharing / content sharing (Anyview Cast, DMR) | Settings → System → Application Settings | Off if you don't cast |
| Bluetooth | Settings → System → Bluetooth | Off if unused |
| VIDAA account | Settings → Account | Sign out (only if no app needs it) |

## DNS (only for the NextDNS setup)

Settings → Network → Network Configuration → IP Settings → **Manual**.

1. Before switching, write down the IP address, subnet mask and gateway shown under **Auto**.
2. Switch to Manual and keep those same values.
3. Set **DNS 1** and **DNS 2** to the two NextDNS IPv4 addresses from your NextDNS **Setup** page (Linked IP section).
4. Don't put a public DNS such as 8.8.8.8 in DNS 2: it would let blocked lookups through.

Phone-hotspot catch: some Android phones choose a new hotspot subnet each time the hotspot restarts. If the TV says "no internet" after that, switch IP Settings back to **Auto**, note the new values, and repeat. An iPhone hotspot always uses `172.20.10.x`, so this doesn't happen there.

## To undo

Set IP Settings back to **Auto**. Re-enable any consent from the same menus.

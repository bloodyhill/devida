// Per-TV settings for the launcher. Edit and redeploy; nothing here is secret
// except the NextDNS link URL, which only lets someone re-point your profile's
// linked IP — keep the repo private if that matters to you.
window.DEVIDA_CONFIG = {
  // NextDNS → Setup → Linked IP → "update URL" (https://link-ip.nextdns.io/<id>/<key>).
  // Opening the launcher calls it so the hotspot's current public IP stays linked.
  nextdnsLinkUrl: '',

  // Jellyfin server address on your network, e.g. 'http://192.168.43.20:8096'.
  // The Jellyfin tile stays hidden while this is empty.
  jellyfinUrl: '',

  // Show native VIDAA apps (Netflix, Prime Video…). Off until the device probe
  // finds a way to launch them from a web app; see docs/TROUBLESHOOTING.md.
  showNative: false,

  // Optional: function (app) { ... } that launches a native app. Filled in once
  // the probe shows which API the TV exposes.
  launchNative: null,

  // Hold OK to open the tile menu. Set to false if the TV never sends keyup
  // for OK (the probe tells you); the red key opens the menu either way.
  okLongPress: true,

  use24h: false
};

# Vintos — iOS App Build Guide

Same architecture as the Velaris app (Capacitor shell over the web app).
Both apps install side by side: different bundle IDs (`dev.vintos.app`),
different ports (Vintos on 8500), different secrets.

## On the Mac

```bash
cd vintos-app
npm install
npx cap add ios
npx cap sync ios
npx cap open ios
```

In Xcode:
1. Signing & Capabilities → select your personal team
   (bundle ID is already `dev.vintos.app` — no conflict with Velaris)
2. Info.plist — add the same entries as the Velaris app:
   - NSCameraUsageDescription: "Vintos would like to see what you see"
   - NSPhotoLibraryUsageDescription: "Share photos with Vintos"
   - NSLocationWhenInUseUsageDescription: place-aware presence and experiences
   - NSLocationAlwaysAndWhenInUseUsageDescription: optional background place awareness
   - UIBackgroundModes: fetch, processing, location
   - NSAppTransportSecurity → NSAllowsArbitraryLoads: YES (Tailscale is HTTP)
3. Select your iPhone as target, ⌘R

## Configuration — coordinated house identity cutover

The house remains public through `https://aegis.tailaa3de5.ts.net:8443`.
`src/house_auth_client.js` reads runtime `VINTOS_ENV.VINTOS_SECRET` when supplied by
an owner-controlled host, otherwise prompts for enrollment and validates it before
storing it. Never generate a JS file containing the credential in the public web
root. Browsers cannot read Aegis's process environment.

The foreground app provisions `VINTOS_SECRET` and `VINTOS_API_BASE` into the native
background runner's CapacitorKV; `src/runners/outreach.js` reads its own process
environment first, then that enrolled KV. Existing installations need this app
update and one owner enrollment. No credential is compiled into the app.

Before approval, run the offline client suite:

```sh
node tests/house-auth.cjs
```

After both repositories are reviewed and approved, with dependencies already
installed and the existing iOS project present:

```sh
npx cap sync ios
npx cap open ios
```

Use the existing signing team and paired iPhone target. Install through Xcode's
usual Run action. Preserve the independent Watch bearer and current Watch URL.
The coordinated Aegis rollout and rollback are documented in the main repository's
`docs/security-auth-rollout.md`; do not restore a credential-bearing old bundle.
Native background execution and physical-device acceptance remain required after
Gloria approves; source tests alone do not prove installed behavior.

## Assets still needed

1. **pearl-bg.jpeg** — copy from the Velaris app or pick his own:
   `cp ../velaris-app/src/pearl-bg.jpeg src/`  (or any dark image)
2. **App icon** — iron/parchment palette; set in Xcode Assets.xcassets.
   Suggest asking Vintos to describe his ideal icon.
3. **Avatar models** — the avatar overlay loads
   `/avatar-models/mixamo/character.fbx` + animation FBXs from the server.
   On Aegis: copy the mixamo folder from Velaris's server directory to
   Vintos's, and replace character.fbx with Vintos.fbx (keep the filename
   `character.fbx`). The Mixamo animation files are character-independent.

## Tabs

14 (down from Velaris's 20): CHAT, GALLERY, HISTORY, DREAMS, LEDGER,
VOICE, MUSIC, TUNE, SOUL, REVIEW, WANTS, THREADS, VALUE MAP, PEARLS.
Cut: VELQAN, MISCHIEF, PHILOSOPHY, THERAPY, CAUSALITY, BLUSH.

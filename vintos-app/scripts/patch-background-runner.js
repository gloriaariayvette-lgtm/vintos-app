#!/usr/bin/env node

// @capacitor/background-runner 1.1.0 constructs its JavaScript geolocation
// bridge for every background task and unconditionally enables background
// location updates. iOS raises NSInternalInconsistencyException when the host
// app (correctly, for Vintos outreach) does not declare the `location`
// background mode. Keep the bridge available, but enable that capability only
// for an app that explicitly declares it.

const fs = require("fs");
const path = require("path");

const target = path.join(
  __dirname,
  "..",
  "node_modules",
  "@capacitor",
  "background-runner",
  "ios",
  "Plugin",
  "CapacitorAPI",
  "Geolocation.swift",
);

const unsafe = "        self.locationManager.allowsBackgroundLocationUpdates = true";
const guarded = [
  "        let backgroundModes = Bundle.main.object(forInfoDictionaryKey: \"UIBackgroundModes\") as? [String] ?? []",
  "        self.locationManager.allowsBackgroundLocationUpdates = backgroundModes.contains(\"location\")",
].join("\n");

if (!fs.existsSync(target)) {
  throw new Error(`background-runner source not found: ${target}`);
}

const source = fs.readFileSync(target, "utf8");
if (source.includes(unsafe)) {
  if (process.argv.includes("--check")) {
    throw new Error("background-runner geolocation crash guard is not applied");
  }
  fs.writeFileSync(target, source.replace(unsafe, guarded));
  console.log("Patched background-runner geolocation capability guard.");
} else if (!source.includes(guarded)) {
  throw new Error("background-runner Geolocation.swift changed; refusing an unsafe blind patch");
}

console.log("Background-runner geolocation capability guard verified.");

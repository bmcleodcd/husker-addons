# Husker's Add-ons

Kodi utilities from Husker. Prepared for publication at
https://bmcleodcd.github.io/husker-addons/ (deployment pending).

Repository ID: `repository.husker`. Display name: **Husker's Add-ons**.

## Build locally

Requires Python 3.9 or later; no third-party packages.

```powershell
python build.py --base-url https://bmcleodcd.github.io/husker-addons
```

This validates Python syntax, packages the add-ons and generates `docs/addons.xml`
and its MD5 change marker. It does not contact Kodi or any online service.
ZIPs use fixed timestamps for repeatable builds. Existing release ZIPs are retained;
always bump the add-on version before changing a released package.

The repository definition is in `repository/addon.xml.in`. Use the full build
command above to include the repository installer. Omitting the URL builds only
the individual add-ons.
The battery ZIP can be installed manually, but has not been tested in Kodi yet.

## First add-on

`script.controller.batteries` 1.0.1 was extracted from the original local installer
without executing it. The add-on ID is preserved for future upgrades. The provider
is now Husker; personal Bluetooth address mappings were removed from this copy.
Discovered controllers use a label based on the last characters of their address.
With no controllers connected, the dialog currently shows only the approximation
notice; configurable controller names and clearer empty-state text can follow.

This is a Linux utility for Sony controllers exposed through
`/sys/class/power_supply/sony_controller_battery_*`, not a universal controller
battery reader. It retains the original low/critical alerts and persistence.
Existing installations and their saved alert state have not been touched.

## When ready to publish

1. Target: `bmcleodcd/husker-addons`, Pages URL as above.
2. Review licensing, metadata, artwork and the add-on on an actual Kodi box.
3. Run `python build.py --base-url https://bmcleodcd.github.io/husker-addons`
   using the real URL. This generates the repository ZIP and includes it in the
   catalogue so the repository itself can receive updates.
4. Create a separate GitHub project containing **only this folder**. The parent
   maintenance workspace contains machine backups, credentials and private data;
   do not publish the parent workspace.
5. Publish `docs/` through Pages, verify all catalogue/package URLs, then install
   `docs/repository.husker/repository.husker-1.0.0.zip` on a test Kodi box.
6. Verify install, update discovery and battery alerts before sharing the link.

To add future add-ons, place each source in `addons/<addon-id>/` with its own
`addon.xml`, then rebuild. Keep old releases available for rollback.

## Wi-Fi manager

`script.husker.wifi` 1.3.0 is included in the catalogue and packaged under
`docs/script.husker.wifi/`. Installed, enabled and tested on Tinybox on
18 October 2026, including live incorrect-password recovery and successful
reconnection. See its README for administrator helper setup and limitations.
Publication is pending GitHub authentication; the Pages URL is now configured
in the release build command.

The catalogue MD5 is Kodi's change marker, not a package security signature.
`hashes=false` avoids relying on content-hash HTTP headers that static hosting
does not necessarily supply. Use HTTPS for hosting.

Reference: https://kodi.wiki/view/Add-on_repositories

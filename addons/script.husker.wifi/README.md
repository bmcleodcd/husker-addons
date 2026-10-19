# Wi-Fi manager 1.3.0

Open **Programs → Wi-Fi manager**, or the **Wi-Fi manager** favourite.

Shows the connected network, Wi-Fi IP address, signal in dBm and negotiated
wireless link rate in Mbps. A less negative dBm value means a stronger signal.
Link rate is not measured internet throughput. The persistent window stays open
while scanning, loading passwords and connecting, with an inline activity message.
Choose **Scan networks**, then select a network. The current network is selected
on opening. Saved Netplan passwords are prefilled and masked by default.
**Show password** reveals the password; **Hide password** masks it again.
**Edit password** opens a prefilled keyboard. Cancel leaves the value unchanged.
Choose **Connect** to apply it. Failures leave the window and entered password
available for editing and retry; the previous connection is restored where possible.
Refresh updates the readings. The add-on keeps passwords in memory and never
includes them in status messages or logs.

Supports open, WPA/WPA2 Personal and WPA3 SAE networks on Linux with
wpa_supplicant and Netplan. Enterprise, WEP and hidden networks are not supported.
Uses the first wireless adapter. Successful connections replace that adapter's
Netplan access-point list, leaving Ethernet and other interface settings intact.
Original Netplan files are backed up, root-only, in `/var/backups/husker-wifi/`.
Passwords are sent through a local socket, never shell arguments or addon settings.
Netplan stores the saved credentials in root-only configuration files.

## Administrator setup

Installing the Kodi ZIP alone cannot grant control of the host's networking.
Review and run `sudo sh setup/install.sh` on the host. Requires Python 3,
python3-yaml, Netplan, systemd and wpa_supplicant. The supplied setup targets
the Linux account `kodi`, home `/home/kodi`, with Kodi data at `~/.kodi`.
Adjust the unit and sudoers account for another installation before running it.
The helper is copied to `/usr/local/sbin/husker-wifi`, owned by root, and is
not automatically updated from Kodi's writable add-on directory.

The socket is private to the kodi account. Kodi Flatpak accesses it through its
existing profile directory, without granting general host-command access.
Native Kodi can also use the restricted, no-arguments sudo helper.

To remove host integration: stop/disable `husker-wifi.socket`, remove its socket
and service unit, `/etc/sudoers.d/husker-wifi`, and `/usr/local/sbin/husker-wifi`,
then reload systemd. Keep the saved Netplan configuration and backups as needed.

## Tinybox validation — 18 October 2026

Installed and enabled on Tinybox's Kodi Flatpak; favourite added; actual Kodi
selection dialog confirmed. Live status and scanning passed. A deliberate wrong
WPA2 password was rejected and the original network restored. Reconnecting with
the existing correct password passed, including Netplan generation and DHCP IP.
Parser and timeout/restoration checks also passed. WPA3, other access points and
persistence after an actual reboot have not been tested.

Version 1.1.1 verified the same window ID before, during and after a live scan,
with inline scanning and completion messages. Saved-password prefill and the
show/hide control passed on Tinybox without writing the password to diagnostics.

Version 1.1.1 bundles its own opaque panel and button texture, and dims Kodi
behind the dialog. It no longer depends on the active skin providing white.png.


## MAC address override — 1.2.0

The MAC override starts with the current Wi-Fi MAC. Choose **Edit MAC**, then
**Apply MAC** to change it. **Restore hardware MAC** removes the saved override
and restores the permanent address. Settings apply to the adapter, not an SSID.
Changes briefly disconnect Wi-Fi and attempt reconnection. A failed change
restores the previous MAC. Invalid, zero, broadcast and multicast addresses are
rejected. Controls are disabled if the permanent MAC or host tools are unavailable;
other driver restrictions are detected on apply. Avoid addresses already in use.

Tinybox passed a live temporary override, Wi-Fi reconnection, Netplan generation
and hardware restoration. The final state uses its original hardware MAC.
Overrides are saved for reboot; an actual reboot has not been tested.


## Share Wi-Fi QR code — 1.3.0

Choose **Share Wi-Fi QR code** to display the currently connected network in a
large, high-contrast QR code. Scan it with a compatible phone camera to join.
The code uses the saved connection password, not an unapplied edit in the window.
Open, WPA/WPA2 Personal and WPA3 SAE payloads are supported; phone support for
WPA3 QR codes varies. Sharing requires a current Wi-Fi connection and, for secured
networks, a saved password. Enterprise networks cannot be shared this way.

The QR contains the password: anyone who can scan or photograph it can use it.
Generation is entirely offline. A private temporary PNG (mode 0600) is deleted
when the QR dialog closes. No credentials are sent to a QR website or written to
logs. A force-killed Kodi process may leave its temporary image in Kodi's temp
folder. The MIT-licensed Project Nayuki qrcodegen 1.8.0 encoder is bundled as
qrcodegen.py, including its copyright and license notice; no extra package install
is needed on Kodi.

Independent ZXing decoding tests passed with synthetic WPA2, SAE, open, Unicode,
escaped punctuation and maximum normal credential sizes. Tinybox's actual QR
screen and temporary-file permissions/removal were verified without exporting its
Wi-Fi credentials. A phone joining the real network has not been tested.

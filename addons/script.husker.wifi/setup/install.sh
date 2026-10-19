#!/bin/sh
set -eu
# Run as root; never execute a privileged helper directly from Kodi's writable directory.
test "$(id -u)" = 0
cd "$(dirname "$0")"
python3 -I -c 'import yaml'
test -x /usr/sbin/netplan
install -o root -g root -m 0755 husker-wifi /usr/local/sbin/husker-wifi
printf '%s\n' 'kodi ALL=(root) NOPASSWD: /usr/local/sbin/husker-wifi ""' > /etc/sudoers.d/husker-wifi
chmod 0440 /etc/sudoers.d/husker-wifi
visudo -cf /etc/sudoers.d/husker-wifi
install -o root -g root -m 0644 husker-wifi.socket husker-wifi@.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now husker-wifi.socket

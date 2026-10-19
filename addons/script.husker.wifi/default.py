import json
import subprocess
import socket
from pathlib import Path
import xbmcgui
import xbmcvfs
import xbmc
import xbmcaddon
import threading
import queue
import tempfile
import os
from wifiqr import payload as wifi_payload, png as qr_png

TITLE = 'Wi-Fi manager'
dialog = xbmcgui.Dialog()


def call(action, **values):
    try:
        endpoint = Path(xbmcvfs.translatePath('special://profile/husker-wifi.sock'))
        if endpoint.exists():
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(115)
                client.connect(str(endpoint))
                client.sendall(json.dumps(dict(action=action, **values)).encode())
                client.shutdown(socket.SHUT_WR)
                chunks = []
                while True:
                    chunk = client.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                data = json.loads(b''.join(chunks))
                if 'error' in data:
                    raise RuntimeError(data['error'])
                return data
        result = subprocess.run(['sudo', '-n', '/usr/local/sbin/husker-wifi'],
                                input=json.dumps(dict(action=action, **values)),
                                text=True, capture_output=True, timeout=115)
        if result.returncode:
            raise RuntimeError('Wi-Fi helper unavailable. Ask an administrator to install the helper from this add-on’s setup folder.')
        data = json.loads(result.stdout)
        if 'error' in data:
            raise RuntimeError(data['error'])
        return data
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise RuntimeError('Cannot communicate with the Wi-Fi helper.') from error


class ShareWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, image_path, network):
        super().__init__(*args)
        self.image_path = image_path
        self.network = network

    def onInit(self):
        self.getControl(41).setImage(self.image_path)
        self.getControl(42).setLabel(self.network)
        self.setFocusId(43)

    def onClick(self, control):
        if control == 43:
            self.getControl(41).setImage('')
            self.close()

    def onAction(self, action):
        if action.getId() in (9, 10, 92):
            self.getControl(41).setImage('')
            self.close()


def share_data():
    status = call('status')['status']
    password = call('password', ssid=status.get('ssid', ''))['password'] if status.get('ssid') else ''
    return {'network': status.get('ssid', ''), 'image': qr_png(wifi_payload(status, password))}


class WifiWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args):
        super().__init__(*args)
        self.pending = queue.Queue()
        self.busy = False
        self.closed = False
        self.ready = False
        self.networks = []
        self.selected = None
        self.password = ''
        self.visible_password = False
        self.current_ssid = None
        self.mac_value = ''
        self.mac = {}

    def onInit(self):
        self.ready = True
        self.setFocusId(20)
        self.start('Reading connection status…', lambda: call('status'), self.show_status)

    def message(self, text):
        self.getControl(12).setText(text)

    def start(self, message, operation, complete):
        if self.busy or self.closed:
            return
        self.busy = True
        self.message(message)
        for control in (20, 21, 22, 23, 24, 26, 27, 28, 29, 30):
            self.getControl(control).setEnabled(False)
        def worker():
            try:
                result = operation()
                self.pending.put((complete, result, None))
            except Exception as error:
                self.pending.put((complete, None, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def tick(self):
        try:
            complete, result, error = self.pending.get_nowait()
        except queue.Empty:
            return
        if self.closed:
            return
        self.busy = False
        for control in (20, 21, 22, 23, 24, 26, 27, 28, 29, 30):
            self.getControl(control).setEnabled(True)
        if error:
            self.message(error)
        else:
            complete(result)
        for control in (26, 27, 28):
            self.getControl(control).setEnabled(not self.busy and self.mac.get('available', False))
        if not self.busy and self.getFocusId() not in (20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30):
            self.setFocusId(20)

    def show_status(self, data):
        status, signal = data['status'], data['signal']
        self.current_ssid = status.get('ssid')
        self.mac = data.get('mac', {})
        self.mac_value = self.mac.get('current', '')
        self.render_mac()
        self.getControl(11).setText('Network: {}   |   IP: {}\nSignal: {} dBm   |   Link speed: {} Mbps'.format(
            status.get('ssid', 'Disconnected'), status.get('ip_address', '—'),
            signal.get('RSSI', '—'), signal.get('LINKSPEED', '—')))
        if self.selected is None and self.current_ssid:
            self.selected = {'ssid': self.current_ssid}
            self.start('Loading saved Wi-Fi password…',
                       lambda: call('password', ssid=self.current_ssid), self.loaded_password)
        else:
            self.message('Ready. Select a network or scan for nearby Wi-Fi.')

    def render_mac(self):
        self.getControl(16).setLabel('MAC override: {}   |   Hardware: {}'.format(
            self.mac_value or 'Unavailable', self.mac.get('permanent') or 'Unavailable'))
        self.getControl(17).setLabel('Applying a MAC briefly disconnects Wi-Fi. Driver support is checked on apply.'
            if self.mac.get('available') else 'MAC override is unavailable on this adapter or host.')

    def loaded_password(self, result):
        self.password = result.get('password', '')
        self.visible_password = False
        self.render_password()
        self.message('Saved password loaded. Choose Show password to view it.' if self.password else
                     'No saved password for this network. Choose Edit password to enter one.')

    def render_password(self):
        name = self.selected['ssid'] if self.selected else 'Select a network'
        self.getControl(13).setLabel('Selected network: ' + name)
        value = self.password if self.visible_password else ('•' * min(len(self.password), 16))
        self.getControl(14).setText('Password: ' + (value or '(empty)'))
        self.getControl(23).setLabel('Hide password' if self.visible_password else 'Show password')

    def scanned(self, result):
        self.networks = result['networks']
        listing = self.getControl(30)
        listing.reset()
        listing.addItems([xbmcgui.ListItem(label='{}   |   {} dBm   |   {}'.format(
            n['ssid'], n['signal'], n['flags'])) for n in self.networks])
        self.message('Found {} networks. Select one to load its saved password.'.format(len(self.networks)))
        if self.networks:
            self.setFocusId(30)

    def connected(self, result):
        message = result['message']
        def refreshed(data):
            self.show_status(data)
            self.message(message + ('' if result['ok'] else '\nEdit the password, then choose Connect to retry.'))
        self.start('Updating connection details…', lambda: call('status'), refreshed)

    def onClick(self, control):
        if control == 25:
            self.finish()
            return
        if self.busy:
            return
        if control == 20:
            self.start('Scanning nearby Wi-Fi networks…', lambda: call('scan'), self.scanned)
        elif control == 21:
            self.start('Refreshing connection details…', lambda: call('status'), self.show_status)
        elif control == 30:
            index = self.getControl(30).getSelectedPosition()
            if 0 <= index < len(self.networks):
                self.selected = self.networks[index]
                self.password = ''
                self.visible_password = False
                self.render_password()
                ssid = self.selected['ssid']
                self.start('Loading saved password for ' + ssid + '…',
                           lambda: call('password', ssid=ssid), self.loaded_password)
        elif control == 22 and self.selected:
            keyboard = xbmc.Keyboard(self.password, 'Password for ' + self.selected['ssid'], True)
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.password = keyboard.getText()
                self.render_password()
                self.message('Password updated here. Choose Connect to apply it.')
        elif control == 23:
            self.visible_password = not self.visible_password
            self.render_password()
        elif control == 29:
            self.start('Preparing a QR code for the currently connected Wi-Fi…', share_data, self.show_share)
        elif control == 26:
            keyboard = xbmc.Keyboard(self.mac_value, 'Wi-Fi MAC override (XX:XX:XX:XX:XX:XX)', False)
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.mac_value = keyboard.getText().strip()
                self.render_mac()
                self.message('MAC edited. Choose Apply MAC to use and save it.')
        elif control in (27, 28):
            value = self.mac_value
            restore = control == 28
            self.start('Restoring hardware MAC and reconnecting Wi-Fi…' if restore else
                       'Applying MAC override and reconnecting Wi-Fi…',
                       lambda: call('mac', mac=value, restore=restore), self.mac_changed)
        elif control == 24 and self.selected:
            ssid, password = self.selected['ssid'], self.password
            self.start('Connecting to ' + ssid + '… Checking password and waiting for the connection.',
                       lambda: call('connect', ssid=ssid, password=password), self.connected)

    def show_share(self, result):
        directory = xbmcvfs.translatePath('special://temp/')
        descriptor, filename = tempfile.mkstemp(prefix='husker-wifi-share-', suffix='.png', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(result['image'])
            result['image'] = b''
            addon = xbmcaddon.Addon()
            sharing = ShareWindow('wifi-share.xml', addon.getAddonInfo('path'), 'Default', '720p',
                                  image_path=filename, network=result['network'])
            try:
                sharing.doModal()
            finally:
                del sharing
        finally:
            Path(filename).unlink(missing_ok=True)
        self.message('QR sharing closed. The temporary QR image has been removed.')

    def mac_changed(self, result):
        message = result['message']
        def refreshed(data):
            self.show_status(data)
            self.message(message)
        self.start('Refreshing MAC and Wi-Fi details…', lambda: call('status'), refreshed)

    def onAction(self, action):
        if action.getId() in (9, 10, 92):
            self.finish()

    def finish(self):
        if self.busy:
            self.message('Please wait for the current Wi-Fi operation to finish…')
            return
        self.password = ''
        self.visible_password = False
        if self.ready:
            self.getControl(14).setText('')
        self.closed = True
        self.close()


def main():
    addon = xbmcaddon.Addon()
    window = WifiWindow('wifi.xml', addon.getAddonInfo('path'), 'Default', '720p')
    window.show()
    monitor = xbmc.Monitor()
    try:
        while not window.closed and not monitor.waitForAbort(0.1):
            if window.ready:
                window.tick()
    finally:
        window.password = ''
        window.close()
        del window


if __name__ == '__main__':
    main()

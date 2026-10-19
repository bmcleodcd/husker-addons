"""Offline Wi-Fi QR payloads and PNG rendering. No credentials are logged."""
import struct
import zlib
from qrcodegen import QrCode


def escape(value):
    return ''.join('\\' + char if char in '\\;,:"' else char for char in value)


def payload(status, password):
    if status.get('wpa_state') != 'COMPLETED' or not status.get('ssid'):
        raise ValueError('Connect to Wi-Fi before sharing it.')
    security = status.get('key_mgmt', '')
    if security == 'NONE':
        kind = 'nopass'
        password = ''
    elif security in ('WPA2-PSK', 'WPA-PSK', 'WPA2-PSK-SHA256', 'SAE', 'FT-SAE'):
        kind = 'SAE' if security in ('SAE', 'FT-SAE') else 'WPA'
        if not password:
            raise ValueError('No saved password is available for the connected network.')
    else:
        raise ValueError('QR sharing supports open and Personal Wi-Fi networks, not enterprise authentication.')
    return 'WIFI:T:{};S:{};P:{};;'.format(kind, escape(status['ssid']), escape(password))


def png(text, side=480):
    qr = QrCode.encode_text(text, QrCode.Ecc.MEDIUM)
    size = qr.get_size()
    scale = side // (size + 8)
    if scale < 1:
        raise ValueError('Wi-Fi information is too large to display as a QR code.')
    offset = (side - size * scale) // 2
    rows = []
    for y in range(side):
        row = bytearray([0])
        for x in range(side):
            mx, my = (x - offset) // scale, (y - offset) // scale
            dark = 0 <= mx < size and 0 <= my < size and qr.get_module(mx, my)
            row.append(0 if dark else 255)
        rows.append(row)
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', side, side, 8, 0, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))

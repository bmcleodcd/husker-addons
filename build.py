"""Build locally only. No network requests, uploads or deployment commands."""
import argparse
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent


def package(folder, manifest, output):
    addon_id, version = manifest.attrib['id'], manifest.attrib['version']
    if not re.fullmatch(r'[a-z0-9._-]+', addon_id) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', version):
        raise ValueError('Invalid add-on ID or version')
    destination = output / addon_id
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f'{addon_id}-{version}.zip'
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as zip_file:
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'Symlinks are not supported: {path}')
            if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            data = path.read_bytes()
            if path.suffix == '.py':
                compile(data, str(path), 'exec')
            info = ZipInfo(f'{addon_id}/{path.relative_to(folder).as_posix()}', (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zip_file.writestr(info, data)
    print(archive.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Final HTTPS directory URL; enables repository ZIP generation')
    args = parser.parse_args()
    base = args.base_url.rstrip('/') if args.base_url else None
    if base:
        url = urlsplit(base)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            parser.error('--base-url must be an HTTPS URL without credentials, query or fragment')
    output = ROOT / 'docs'
    output.mkdir(exist_ok=True)
    catalogue = ET.Element('addons')
    for folder in sorted((ROOT / 'addons').iterdir()):
        if not folder.is_dir():
            continue
        manifest = ET.parse(folder / 'addon.xml').getroot()
        if folder.name != manifest.attrib['id']:
            raise ValueError(f'Folder and add-on ID differ: {folder}')
        package(folder, manifest, output)
        catalogue.append(manifest)
    if base:
        folder = ROOT / '.preview' / 'repository.husker'
        folder.mkdir(parents=True, exist_ok=True)
        manifest = ET.fromstring((ROOT / 'repository/addon.xml.in').read_text(encoding='utf-8'))
        for element in manifest.iter():
            if element.text and '@BASE_URL@' in element.text:
                element.text = element.text.replace('@BASE_URL@', base)
        ET.ElementTree(manifest).write(folder / 'addon.xml', encoding='utf-8', xml_declaration=True)
        package(folder, manifest, output)
        catalogue.append(manifest)
    ET.indent(catalogue)
    content = ET.tostring(catalogue, encoding='utf-8', xml_declaration=True) + b'\n'
    (output / 'addons.xml').write_bytes(content)
    (output / 'addons.xml.md5').write_text(hashlib.md5(content).hexdigest(), encoding='ascii')
    (output / '.nojekyll').touch()
    print('Local build complete. Nothing uploaded.')
    if not base:
        print('Hosting URL unset: repository installer intentionally not generated.')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Download a portable wkhtmltopdf Windows zip and extract wkhtmltopdf.exe into ./bin/
This script is safe to run on Windows and will not require admin privileges.
"""
import os
import sys
import shutil
import zipfile
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BIN_DIR = os.path.join(BASE_DIR, 'bin')

# Release chosen: wkhtmltopdf 0.12.6-1 msvc2015 win64 (portable zip)
# Source: https://github.com/wkhtmltopdf/packaging/releases
URL = 'https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.zip'

def download(url, dest):
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; RadGestMat-installer)'
    })
    try:
        with urlopen(req) as r, open(dest, 'wb') as f:
            shutil.copyfileobj(r, f)
        return dest
    except HTTPError as e:
        print('HTTP Error:', e.code, e.reason)
    except URLError as e:
        print('URL Error:', e.reason)
    return None


def extract_wkzip(zip_path, target_bin_dir):
    with zipfile.ZipFile(zip_path, 'r') as z:
        members = z.namelist()
        # find the wkhtmltopdf.exe entry
        exe_candidates = [m for m in members if m.lower().endswith('wkhtmltopdf.exe')]
        if not exe_candidates:
            print('No wkhtmltopdf.exe found in zip')
            return False
        # ensure bin dir exists
        os.makedirs(target_bin_dir, exist_ok=True)
        for cand in exe_candidates:
            # extract the exe to bin
            dest_path = os.path.join(target_bin_dir, os.path.basename(cand))
            with z.open(cand) as src, open(dest_path, 'wb') as out:
                shutil.copyfileobj(src, out)
            print('Extracted', dest_path)
        return True


def main():
    if sys.platform != 'win32' and not sys.platform.startswith('win'):
        print('Warning: this installer targets Windows builds; proceeding anyway.')
    os.makedirs(BIN_DIR, exist_ok=True)
    archive = os.path.join(BIN_DIR, 'wkhtmltopdf.zip')
    print('Downloading', URL)
    out = download(URL, archive)
    if not out:
        print('Download failed')
        sys.exit(2)
    ok = extract_wkzip(archive, BIN_DIR)
    if not ok:
        print('Extraction failed')
        sys.exit(3)
    # make executable flag (no-op on Windows but okay)
    exe_path = os.path.join(BIN_DIR, 'wkhtmltopdf.exe')
    if os.path.exists(exe_path):
        try:
            os.chmod(exe_path, 0o755)
        except Exception:
            pass
        print('wkhtmltopdf installed to', exe_path)
        print('You can now request PDFs; the app will prefer ./bin/wkhtmltopdf.exe')
        sys.exit(0)
    else:
        print('Expected binary not found after extraction')
        sys.exit(4)

if __name__ == '__main__':
    main()

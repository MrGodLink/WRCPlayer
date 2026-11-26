# Third-party components

WRCPlayer's own code is MIT-licensed (see `LICENSE`). It depends on the
following components, which keep their own licenses. This is an overview, not
legal advice: check the exact versions you bundle.

| Component | Use | License |
|-----------|-----|---------|
| PySide6 / Qt | GUI, Qt Multimedia | LGPL-3.0 (also GPL / commercial) |
| FFmpeg (inside Qt Multimedia) | Video and fallback audio decoding | LGPL-2.1+ or GPL, depending on the build |
| pywin32 | COM automation of Windows Media Player | PSF-style license |
| Pillow (build only) | Writes `assets/app_icon.ico` | HPND |
| PyInstaller (build only) | Packaging | GPL-2.0 with bootloader exception |

**Windows Media Player Legacy** is *not* distributed with WRCPlayer: it is
used through the COM interface if the user's Windows already provides it.

## If you distribute a built `.exe`
- Keep the license texts of PySide6/Qt and FFmpeg with the build.
- Prefer the folder build (`build.bat`, no `--onefile`): the LGPL shared
  libraries stay visible and replaceable.
- Point to the upstream sources: <https://doc.qt.io/qtforpython-6/> and
  <https://ffmpeg.org/>.

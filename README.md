# Muktadha

A Windows system-tray environment switcher. Quickly switch between work, chill, or custom modes — launching apps, opening URLs, and closing processes with one click.

## Features

- **System tray icon** — right-click to switch modes
- **Per-mode config** — apps to launch, URLs to open, processes to close
- **Settings GUI** — tabbed window to manage each mode's apps, URLs, and close rules
- **Browse installed apps** — scan Start Menu for installed applications
- **Single instance** — only one instance runs at a time
- **Run at startup** — toggle from the tray menu
- **Splash screen** — shown on startup (frozen build only)
- **Portable build** — single-file `.exe` via PyInstaller

## Usage

1. Run `build.py` to generate `dist/Muktadha.exe`
2. Launch `Muktadha.exe` — the tray icon appears
3. Right-click the tray icon to:
   - Switch modes
   - Open Settings
   - Toggle "Run at startup"
   - Exit

## Requirements

- Python 3.10+
- `pystray`, `Pillow`, `psutil` (see `requirements.txt`)

## Build

```bash
python build.py
```

Output: `dist/Muktadha.exe` (single file, ~55 MB)

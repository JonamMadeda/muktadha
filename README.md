# Muktadha

[![Download](https://img.shields.io/badge/Download-v1.1.0-blue?style=for-the-badge&logo=github)](https://github.com/JonamMadeda/muktadha/releases/latest)

A Windows system-tray environment switcher. Quickly switch between work, chill, or custom modes — launching apps, opening URLs, and closing processes with one click.

## Features

- **System tray icon** — right-click to switch modes
- **Per-mode config** — apps to launch, URLs to open, processes to close
- **Settings GUI** — tabbed window to manage each mode's apps, URLs, and close rules
- **Browse installed apps** — scan Start Menu for installed applications
- **Single instance** — only one instance runs at a time
- **Run at startup** — toggle from the tray menu
- **Auto-update** — built-in check for new releases
- **Splash screen** — shown on startup
- **Proper installer** — installs to Program Files, uninstall via Control Panel

## Install

Download the latest `Muktadha_Installer.exe` from [Releases](https://github.com/JonamMadeda/muktadha/releases/latest) and run it.

## Build from Source

```bash
pip install -r requirements.txt
python build.py          # builds dist/Muktadha.exe
python release.py 1.1.0  # or use Inno Setup for the installer
```

## Requirements

- Python 3.10+
- `pystray`, `Pillow`, `psutil` (see `requirements.txt`)

# CDDA Mac Launcher

A modern, user-friendly launcher for Cataclysm: Dark Days Ahead and Bright Nights on macOS.

## Features

- Easy installation and launching of both CDDA Experimental and Stable builds
- Support for Bright Nights
- Automatic version checking and updates
- One-click download and installation
- Save data preservation between updates
- Direct access to patch notes
- GitHub integration for release notes
- Clean, modern interface using CustomTkinter

## Requirements

- macOS
- Python 3.x
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/MacCDDALauncher.git
cd MacCDDALauncher
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the launcher:
```bash
python cdda_launcher.py
```

## Usage

- Choose between Cataclysm: DDA and Bright Nights using the top buttons
- View available versions and their status
- Download and install new versions with one click
- Launch the game directly from the launcher
- View patch notes in the app or on GitHub
- Saves and user data are automatically preserved between updates

## Game Installation Location

Games are installed to:
`~/Library/Application Support/Cataclysm/`

With subdirectories:
- `experimental/` - For CDDA experimental builds
- `stable/` - For CDDA stable builds
- `bn/` - For Bright Nights builds

## Building the App

To build the standalone app:
```bash
python build_app.py
```

To create a DMG installer:
```bash
python build_dmg.py
```

## License

MIT License - See LICENSE file for details 
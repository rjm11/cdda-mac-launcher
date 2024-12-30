# CDDA Mac Launcher

A native macOS launcher for Cataclysm: Dark Days Ahead and Cataclysm: Bright Nights. Created to fill the gap in Mac-specific launchers for CDDA, providing a simple, clean solution for Mac users to manage and update their game.

## Why This Launcher?

While Cataclysm: DDA and Bright Nights are fantastic games with active communities, Mac users often lack the convenient launcher tools available to Windows users. This project aims to provide Mac users with a native, straightforward way to:
- Keep track of both experimental and stable versions
- Easily update their game without manual DMG handling
- Preserve save data during updates
- View patch notes directly in the launcher
- Switch between CDDA and Bright Nights variants

## Features

- Native macOS integration
- Download and manage both CDDA (experimental and stable) and Bright Nights versions
- Automatic version tracking and updates
- Save game preservation during updates
- Built-in patch notes viewer
- Easy switching between CDDA and Bright Nights
- Modern, clean interface using customtkinter

## Installation

### Option 1: Download Release (Recommended)
1. Download the latest release from the releases page
2. Mount the DMG
3. Drag the app to your Applications folder
4. Launch from Applications or Spotlight

### Option 2: Build from Source
```bash
# Clone the repository
git clone https://github.com/rjm11/cdda-mac-launcher.git
cd cdda-mac-launcher

# Install dependencies
pip install -r requirements.txt

# Build the app
python build_app.py

# Or run directly without building
python cdda_launcher.py
```

## Requirements

- macOS 10.10 or newer
- Python 3.7+ (if building from source)
- Internet connection for version checking and downloads

## Usage

1. Launch the application
2. Choose between CDDA and Bright Nights using the toggle at the top
3. Download your preferred version using the "Download Latest" button
4. Launch the game using the "Launch" button
5. View patch notes in the bottom panel

The launcher will:
- Automatically check for updates
- Show a green checkmark when you have the latest version
- Display yellow text when updates are available
- Preserve your save games during updates
- Store games in `~/Library/Application Support/Cataclysm/`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 
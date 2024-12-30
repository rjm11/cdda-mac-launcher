# CDDA Launcher

A cross-platform launcher for Cataclysm: Dark Days Ahead and Cataclysm: Bright Nights.

## Features

- Download and manage both CDDA (experimental and stable) and Bright Nights versions
- Automatic version tracking and updates
- Save game preservation during updates
- Patch notes viewer
- Easy switching between CDDA and Bright Nights
- Cross-platform support (Windows and macOS)

## Installation

### Windows
1. Download the latest release from the releases page
2. Run the executable

### macOS
1. Download the latest release from the releases page
2. Mount the DMG and drag the app to your Applications folder

### From Source
```bash
# Clone the repository
git clone https://github.com/rjm11/cdda-mac-launcher.git
cd cdda-mac-launcher

# Install dependencies
pip install -r requirements.txt

# Run the launcher
python cdda_launcher.py
```

## Building from Source

### Windows
```bash
# Install requirements
pip install -r requirements.txt

# Build executable
python build_windows.py
```

### macOS
```bash
# Install requirements
pip install -r requirements.txt

# Build app
python build_app.py
```

## Usage

1. Launch the application
2. Choose between CDDA and Bright Nights using the toggle at the top
3. Download your preferred version using the "Download Latest" button
4. Launch the game using the "Launch" button
5. View patch notes in the bottom panel

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 
#!/usr/bin/env python3
import os
import shutil
import subprocess
import plistlib
import urllib.request
import sys
import tempfile

def convert_ico_to_icns():
    if not os.path.exists("AppIcon.ico"):
        return None
        
    print("Converting .ico to .icns format...")
    
    # Create temporary iconset directory
    with tempfile.TemporaryDirectory() as temp_dir:
        iconset_path = os.path.join(temp_dir, "icon.iconset")
        os.makedirs(iconset_path)
        
        # Convert ico to png and resize for different sizes
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            # Convert to both regular and @2x sizes
            subprocess.run([
                "sips",
                "-s", "format", "png",
                "--resampleHeightWidth", str(size), str(size),
                "AppIcon.ico",
                "--out", os.path.join(iconset_path, f"icon_{size}x{size}.png")
            ])
            if size <= 512:  # @2x versions only up to 512 (becomes 1024)
                subprocess.run([
                    "sips",
                    "-s", "format", "png",
                    "--resampleHeightWidth", str(size*2), str(size*2),
                    "AppIcon.ico",
                    "--out", os.path.join(iconset_path, f"icon_{size}x{size}@2x.png")
                ])
        
        # Convert iconset to icns
        subprocess.run(["iconutil", "-c", "icns", iconset_path, "-o", "AppIcon.icns"])
        
        if os.path.exists("AppIcon.icns"):
            print("Successfully converted icon to .icns format")
            return "AppIcon.icns"
    
    return None

def build_app():
    # App bundle structure
    app_name = "CDDA Launcher.app"
    contents_dir = os.path.join(app_name, "Contents")
    macos_dir = os.path.join(contents_dir, "MacOS")
    resources_dir = os.path.join(contents_dir, "Resources")
    
    # Clean any existing bundle
    if os.path.exists(app_name):
        shutil.rmtree(app_name)
    
    # Create directory structure
    os.makedirs(macos_dir)
    os.makedirs(resources_dir)
    
    # Convert icon if needed
    if os.path.exists("AppIcon.ico"):
        icon_path = convert_ico_to_icns()
    else:
        icon_path = "AppIcon.icns" if os.path.exists("AppIcon.icns") else None
    
    # Copy icon if available
    if icon_path and os.path.exists(icon_path):
        shutil.copy(icon_path, os.path.join(resources_dir, "AppIcon.icns"))
        use_icon = True
    else:
        use_icon = False
    
    # Create Info.plist
    info_plist = {
        'CFBundleName': 'CDDA Launcher',
        'CFBundleDisplayName': 'CDDA Launcher',
        'CFBundleIdentifier': 'com.cdda.launcher',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'launcher',
        'LSMinimumSystemVersion': '10.10.0',
        'NSHighResolutionCapable': True,
    }
    
    if use_icon:
        info_plist['CFBundleIconFile'] = 'AppIcon'
    
    with open(os.path.join(contents_dir, 'Info.plist'), 'wb') as f:
        plistlib.dump(info_plist, f)
    
    # Create launcher script
    launcher_script = '''#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="${DIR}/../Resources"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is required but not installed. Please install Python 3 from python.org" buttons {"OK"} default button "OK" with icon stop with title "Python Not Found"'
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    osascript -e 'display dialog "pip3 is required but not installed. Please install pip3" buttons {"OK"} default button "OK" with icon stop with title "pip Not Found"'
    exit 1
fi

# Install requirements if needed
pip3 install -r "${DIR}/../Resources/requirements.txt" > /dev/null 2>&1

# Run the launcher
python3 "${DIR}/../Resources/cdda_launcher.py"
'''
    
    with open(os.path.join(macos_dir, 'launcher'), 'w') as f:
        f.write(launcher_script)
    
    # Make launcher script executable
    os.chmod(os.path.join(macos_dir, 'launcher'), 0o755)
    
    # Copy necessary files to Resources
    shutil.copy('cdda_launcher.py', resources_dir)
    shutil.copy('requirements.txt', resources_dir)
    
    print(f"Created {app_name}")
    
    # Move to Applications if requested
    response = input("Would you like to install the app to /Applications? (y/n): ")
    if response.lower() == 'y':
        if os.path.exists('/Applications/CDDA Launcher.app'):
            shutil.rmtree('/Applications/CDDA Launcher.app')
        shutil.move(app_name, '/Applications/')
        print("Installed to /Applications")

if __name__ == "__main__":
    build_app() 
#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

def install_from_dmg(dmg_path):
    print("\nInstalling to Applications...")
    try:
        # Mount the DMG
        mount_process = subprocess.run(["hdiutil", "attach", str(dmg_path)], 
                                    capture_output=True, text=True)
        
        # Find the mount point
        mount_point = None
        for line in mount_process.stdout.split('\n'):
            if '/Volumes/' in line:
                mount_point = line.split('\t')[-1].strip()
                break
        
        if not mount_point:
            print("Error: Could not find mount point")
            return False
            
        # Find the .app in the mounted DMG
        app_name = "CDDA Launcher.app"
        source_app = Path(mount_point) / app_name
        target_app = Path("/Applications") / app_name
        
        # Remove existing installation if present
        if target_app.exists():
            print("Removing previous installation...")
            shutil.rmtree(target_app)
        
        # Copy the app to Applications
        print("Copying to Applications...")
        shutil.copytree(source_app, target_app, symlinks=True)
        
        # Unmount the DMG
        subprocess.run(["hdiutil", "detach", mount_point], check=True)
        
        print("Installation complete!")
        return True
        
    except Exception as e:
        print(f"Error during installation: {str(e)}")
        return False

def create_dmg():
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Create a temporary directory for DMG creation
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Creating clean app bundle...")
        
        # First build the app, skipping installation
        subprocess.run([sys.executable, "build_app.py", "--skip-install"], check=True)
        
        # Find the app in the current directory
        app_name = "CDDA Launcher.app"
        source_app = script_dir / app_name
        temp_app = Path(temp_dir) / app_name
        
        if not source_app.exists():
            print(f"Error: Could not find {app_name} in the current directory")
            print(f"Looking in: {source_app}")
            print("Current directory contents:")
            for item in script_dir.iterdir():
                print(f"  {item.name}")
            return
        
        # Copy the fresh app to temp directory
        shutil.copytree(source_app, temp_app)
        
        print("Creating DMG...")
        
        # Create DMG name with version
        dmg_name = "CDDA_Launcher_1.0.0.dmg"  # You can update version as needed
        dmg_path = script_dir / dmg_name
        
        # Remove existing DMG if it exists
        if dmg_path.exists():
            dmg_path.unlink()
        
        # Calculate required size (app size + 10MB buffer)
        app_size = sum(f.stat().st_size for f in temp_app.rglob('*') if f.is_file())
        dmg_size = str(int((app_size + 10*1024*1024) / 1024 / 1024))+"m"
        
        # Create DMG directly (without temporary DMG)
        subprocess.run([
            "hdiutil", "create",
            "-size", dmg_size,
            "-srcfolder", str(temp_dir),
            "-volname", "CDDA Launcher",
            "-fs", "HFS+",
            "-format", "UDZO",
            "-imagekey", "zlib-level=9",
            str(dmg_path)
        ], check=True)
        
        print(f"DMG created successfully at: {dmg_path}")
        print("\nThis DMG is clean and ready for distribution!")
        
        # Ask about installation
        response = input("\nWould you like to install the app to Applications? (y/n): ")
        if response.lower() == 'y':
            install_from_dmg(dmg_path)

if __name__ == "__main__":
    create_dmg() 
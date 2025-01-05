import customtkinter as ctk
import requests
import json
import os
import shutil
from datetime import datetime
import threading
import webbrowser
import subprocess
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from tqdm import tqdm
import time
import socket
import sys

class SingleInstance:
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_path = os.path.expanduser('~/.cdda_launcher.sock')
        
        try:
            # Try to connect to an existing instance
            self.sock.connect(self.socket_path)
            # If we can connect, another instance exists
            self.sock.send(b'show')  # Tell the other instance to show itself
            self.sock.close()
            print("Another instance is already running")
            os._exit(0)  # Force immediate exit
        except (socket.error, ConnectionRefusedError):
            # No other instance exists, clean up any stale socket and set up the listener
            if os.path.exists(self.socket_path):
                try:
                    os.unlink(self.socket_path)
                except OSError:
                    pass
            try:
                self.sock.bind(self.socket_path)
                self.sock.listen(1)
                self.start_listener()
            except Exception as e:
                print(f"Error setting up socket: {e}")
                self.sock.close()
                if os.path.exists(self.socket_path):
                    os.unlink(self.socket_path)
                os._exit(1)  # Force immediate exit on error

    def start_listener(self):
        def listen():
            while True:
                try:
                    client, _ = self.sock.accept()
                    data = client.recv(1024)
                    if data == b'show':
                        # Bring window to front
                        if hasattr(self, 'app'):
                            self.app.lift()
                            self.app.focus_force()
                            if hasattr(self.app, 'attributes'):  # Check if running in a window system
                                self.app.attributes('-topmost', True)  # Bring to front
                                self.app.attributes('-topmost', False)  # Allow other windows to go in front again
                    client.close()
                except:
                    break
        
        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()

    def cleanup(self):
        try:
            self.sock.close()
        except:
            pass
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except:
            pass

class CDDALauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Store reference to SingleInstance
        self.single_instance = SingleInstance()
        self.single_instance.app = self
        
        # Configure window
        self.title("CDDA Mac Launcher")
        self.geometry("700x600")  # Wider window to accommodate text
        ctk.set_appearance_mode("system")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Weight for patch notes
        
        # Variables
        self.experimental_version = ctk.StringVar(value="Checking...")
        self.stable_version = ctk.StringVar(value="Checking...")
        self.download_progress = ctk.DoubleVar(value=0)
        self.status_text = ctk.StringVar(value="Ready")
        self.showing_cdda = True  # Track which game page we're showing
        self.latest_experimental_mac_tag = None  # New variable to track last available Mac build
        
        # Setup paths
        self.base_path = os.path.expanduser("~/Library/Application Support/Cataclysm")
        self.experimental_path = os.path.join(self.base_path, "experimental")
        self.stable_path = os.path.join(self.base_path, "stable")
        self.bn_path = os.path.join(self.base_path, "bn")
        self.dcss_path = os.path.join(self.base_path, "dcss")
        self.version_file = os.path.join(self.base_path, "versions.json")
        
        # Create directories if they don't exist
        for path in [self.base_path, self.experimental_path, self.stable_path, self.bn_path, self.dcss_path]:
            os.makedirs(path, exist_ok=True)
        
        # Load saved versions
        self.load_versions()
        
        self._create_ui()
        self.check_versions()

    def load_versions(self):
        # Initialize with None
        self.installed_experimental_version = None
        self.installed_stable_version = None
        self.installed_bn_version = None
        self.installed_dcss_version = None
        
        # Try to load saved versions
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r') as f:
                    versions = json.load(f)
                    self.installed_experimental_version = versions.get('experimental')
                    self.installed_stable_version = versions.get('stable')
                    self.installed_bn_version = versions.get('bn')
                    self.installed_dcss_version = versions.get('dcss')
            except (json.JSONDecodeError, IOError):
                pass  # If there's any error reading, keep the default None values

    def save_versions(self):
        versions = {
            'experimental': self.installed_experimental_version,
            'stable': self.installed_stable_version,
            'bn': self.installed_bn_version,
            'dcss': self.installed_dcss_version
        }
        try:
            with open(self.version_file, 'w') as f:
                json.dump(versions, f)
        except IOError:
            pass  # If we can't save, just continue

    def _create_ui(self):
        # Header with game selector
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=15, pady=(5,2), sticky="ew")  # Slightly more horizontal padding
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Game selector buttons
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(pady=2)
        
        self.cdda_button = ctk.CTkButton(button_frame, 
                                       text="Cataclysm: DDA",
                                       command=lambda: self.switch_game("cdda"),
                                       width=120,
                                       height=28)
        self.cdda_button.pack(side="left", padx=5)
        
        self.bn_button = ctk.CTkButton(button_frame,
                                     text="Bright Nights",
                                     command=lambda: self.switch_game("bn"),
                                     width=120,
                                     height=28)
        self.bn_button.pack(side="left", padx=5)
        
        self.dcss_button = ctk.CTkButton(button_frame,
                                     text="DCSS",
                                     command=lambda: self.switch_game("dcss"),
                                     width=120,
                                     height=28)
        self.dcss_button.pack(side="left", padx=5)
        
        # Create game frames
        self._create_cdda_frame()
        self._create_bn_frame()
        self._create_dcss_frame()
        
        # Initially hide BN and DCSS frames
        self.bn_frame.grid_remove()
        self.dcss_frame.grid_remove()
        
        # Progress bar and status in a separate frame
        self._create_status_frame()
        
        # Patch Notes Frame
        self._create_patch_notes_frame()
        
    def _create_cdda_frame(self):
        # CDDA Frame
        self.cdda_frame = ctk.CTkFrame(self)
        self.cdda_frame.grid(row=1, column=0, padx=15, pady=2, sticky="ew")
        self.cdda_frame.grid_columnconfigure(0, weight=1)
        
        # Version Frame (will show either Experimental or Stable)
        self.version_frame = ctk.CTkFrame(self.cdda_frame)
        self.version_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.version_frame.grid_columnconfigure(1, weight=1)
        
        # Title with refresh and toggle buttons
        title_frame = ctk.CTkFrame(self.version_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=5, pady=2)
        
        self.version_title = ctk.CTkLabel(title_frame, text="Experimental Version:", 
                    font=ctk.CTkFont(weight="bold", size=13))
        self.version_title.pack(side="left", padx=(0,5))
        
        ctk.CTkButton(title_frame,
                     text="↻",
                     command=self.check_versions,
                     width=20,
                     height=20).pack(side="left", padx=2)
        
        ctk.CTkButton(title_frame,
                     text="Switch to Stable",
                     command=self.toggle_cdda_version,
                     width=100,
                     height=20).pack(side="left", padx=2)
        
        # Split version display into two labels
        version_info_frame = ctk.CTkFrame(self.version_frame, fg_color="transparent")
        version_info_frame.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        self.version_latest_label = ctk.CTkLabel(version_info_frame, text="", font=ctk.CTkFont(family="Courier"))
        self.version_latest_label.pack(anchor="w")
        self.version_installed_label = ctk.CTkLabel(version_info_frame, text="", font=ctk.CTkFont(family="Courier"))
        self.version_installed_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(self.version_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=2)
        
        self.download_button = ctk.CTkButton(button_frame, text="Download Latest", 
                     command=lambda: self.download_version("experimental"),
                     width=100,
                     height=28)
        self.download_button.pack(side="left", padx=2)
        
        self.launch_button = ctk.CTkButton(button_frame, text="Launch", 
                     command=lambda: self.launch_game("experimental"),
                     width=80,
                     height=28)
        self.launch_button.pack(side="left", padx=2)
        
        self.folder_button = ctk.CTkButton(button_frame, text="Open Folder", 
                     command=lambda: self.open_folder("experimental"),
                     width=90,
                     height=28)
        self.folder_button.pack(side="left", padx=2)
        
        # Add variable to track current CDDA version type
        self.showing_experimental = True

    def toggle_cdda_version(self):
        self.showing_experimental = not self.showing_experimental
        if self.showing_experimental:
            self.version_title.configure(text="Experimental Version:")
            self.download_button.configure(command=lambda: self.download_version("experimental"))
            self.launch_button.configure(command=lambda: self.launch_game("experimental"))
            self.folder_button.configure(command=lambda: self.open_folder("experimental"))
            title_frame = self.version_title.winfo_parent()
            for widget in ctk.CTkButton.winfo_children(title_frame):
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Switch to Stable":
                    widget.configure(text="Switch to Stable")
        else:
            self.version_title.configure(text="Stable Version:")
            self.download_button.configure(command=lambda: self.download_version("stable"))
            self.launch_button.configure(command=lambda: self.launch_game("stable"))
            self.folder_button.configure(command=lambda: self.open_folder("stable"))
            title_frame = self.version_title.winfo_parent()
            for widget in ctk.CTkButton.winfo_children(title_frame):
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Switch to Experimental":
                    widget.configure(text="Switch to Experimental")
        self.check_installed_versions()

    def check_installed_versions(self):
        exp_version = self.get_version(self.experimental_path, self.installed_experimental_version)
        stable_version = self.get_version(self.stable_path, self.installed_stable_version)
        bn_version = self.get_version(self.bn_path, self.installed_bn_version)
        dcss_version = self.get_version(self.dcss_path, self.installed_dcss_version)
        
        if self.showing_experimental:
            # Update experimental version display
            is_exp_latest = exp_version == self.latest_experimental_mac_tag
            latest_text = f"Latest:         {self.latest_experimental_tag}"
            mac_build_text = f"Mac build:      {self.latest_experimental_mac_tag}"
            installed_text = f"Installed:      {exp_version if exp_version else 'Not installed'}"
            
            if exp_version and is_exp_latest:
                installed_text += " ✓"
            if self.latest_experimental_tag != self.latest_experimental_mac_tag:
                installed_text += "\nLatest Mac Build and Latest Build do not match,\nupdate coming soon"
            
            self.version_latest_label.configure(
                text=f"{latest_text}\n{mac_build_text}",
                text_color=("yellow" if not is_exp_latest else "white"),
                justify="left"
            )
            self.version_installed_label.configure(
                text=installed_text,
                text_color="green" if is_exp_latest else "white",
                justify="left"
            )
        else:
            # Update stable version display
            is_stable_latest = stable_version == self.latest_stable_tag
            latest_text = f"Latest:         {self.latest_stable_tag}"
            installed_text = f"Installed:      {stable_version if stable_version else 'Not installed'}"
            if stable_version and is_stable_latest:
                installed_text += " ✓"
            
            self.version_latest_label.configure(
                text=latest_text,
                text_color=("yellow" if not is_stable_latest else "white"),
                justify="left"
            )
            self.version_installed_label.configure(
                text=installed_text,
                text_color="green" if is_stable_latest else "white",
                justify="left"
            )

    def switch_game(self, game):
        # First, remove all frames
        self.cdda_frame.grid_remove()
        self.bn_frame.grid_remove()
        self.dcss_frame.grid_remove()
        
        # Reset all button colors
        self.cdda_button.configure(fg_color=None)
        self.bn_button.configure(fg_color=None)
        self.dcss_button.configure(fg_color=None)
        
        if game == "cdda":
            self.showing_cdda = True
            self.cdda_frame.grid(row=1, column=0, padx=15, pady=2, sticky="ew")
            self.cdda_button.configure(fg_color=("gray75", "gray25"))
            self.title("CDDA Mac Launcher")
            # Show CDDA patch notes toggle
            self.toggle_button.grid()
            if self.showing_experimental_notes:
                self.patch_notes_label.configure(text="Latest Experimental Patch Notes:")
                self.patch_notes.delete("0.0", "end")
                self.patch_notes.insert("0.0", self.experimental_patch_notes)
            else:
                self.patch_notes_label.configure(text="Latest Stable Patch Notes:")
                self.patch_notes.delete("0.0", "end")
                self.patch_notes.insert("0.0", self.stable_patch_notes)
        elif game == "bn":
            self.showing_cdda = False
            self.bn_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
            self.bn_button.configure(fg_color=("gray75", "gray25"))
            self.title("Bright Nights Mac Launcher")
            # Hide CDDA patch notes toggle and show BN notes
            self.toggle_button.grid_remove()
            self.patch_notes_label.configure(text="Latest Patch Notes:")
            self.patch_notes.delete("0.0", "end")
            self.patch_notes.insert("0.0", self.bn_patch_notes)
        else:  # dcss
            self.showing_cdda = False
            self.dcss_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
            self.dcss_button.configure(fg_color=("gray75", "gray25"))
            self.title("DCSS Launcher")
            # Hide CDDA patch notes toggle and show DCSS notes
            self.toggle_button.grid_remove()
            self.patch_notes_label.configure(text="Latest DCSS Notes:")
            self.patch_notes.delete("0.0", "end")
            self.patch_notes.insert("0.0", self.dcss_patch_notes)

    def toggle_patch_notes(self):
        self.showing_experimental_notes = not self.showing_experimental_notes
        if self.showing_experimental_notes:
            self.patch_notes_label.configure(text="Latest Experimental Patch Notes:")
            self.toggle_button.configure(text="View Stable Notes")
            self.patch_notes.delete("0.0", "end")
            self.patch_notes.insert("0.0", self.experimental_patch_notes)
        else:
            self.patch_notes_label.configure(text="Latest Stable Patch Notes:")
            self.toggle_button.configure(text="View Experimental Notes")
            self.patch_notes.delete("0.0", "end")
            self.patch_notes.insert("0.0", self.stable_patch_notes)

    def get_version(self, path, tracked_version):
        if not os.path.exists(path):
            return None
        
        app_path = os.path.join(path, "Cataclysm.app")
        if not os.path.exists(app_path):
            return None

        return tracked_version if tracked_version else "Unknown Version"

    def check_versions(self):
        def check():
            try:
                # Check experimental version
                exp_response = requests.get("https://api.github.com/repos/CleverRaven/Cataclysm-DDA/releases")
                releases = json.loads(exp_response.text)
                
                # Always set latest tag from the first experimental release
                for release in releases:
                    if "experimental" in release["tag_name"].lower():
                        self.latest_experimental_tag = release['tag_name']
                        break
                
                # Then find the newest Mac build by searching all releases
                found_mac_build = False
                self.latest_experimental_mac_tag = None
                self.latest_experimental_url = None
                
                for release in releases:
                    if "experimental" in release["tag_name"].lower():
                        # Look for Mac build
                        for asset in release["assets"]:
                            name = asset["name"].lower()
                            if "osx" in name and "graphics" in name and "universal" in name and name.endswith(".dmg"):
                                if not found_mac_build:  # Only set these for the first Mac build found
                                    self.latest_experimental_mac_tag = release['tag_name']
                                    self.latest_experimental_url = asset["browser_download_url"]
                                    self.experimental_patch_notes = release.get("body", "No patch notes available")
                                    found_mac_build = True
                                    break
                        
                        if found_mac_build:
                            break
                
                # Update experimental version display
                exp_version = self.get_version(self.experimental_path, self.installed_experimental_version)
                # Compare against Mac build tag instead of latest experimental tag
                is_exp_latest = exp_version == self.latest_experimental_mac_tag
                
                if self.latest_experimental_mac_tag and self.latest_experimental_tag != self.latest_experimental_mac_tag:
                    latest_text = f"Latest: {self.latest_experimental_tag}\nMac build: {self.latest_experimental_mac_tag}"
                    if exp_version != self.latest_experimental_mac_tag:
                        latest_text += "\n(Newer Mac build may come soon)"
                else:
                    latest_text = f"Latest: {self.latest_experimental_tag}"
                
                installed_text = f"Installed: {exp_version if exp_version else 'Not installed'}"
                if exp_version and is_exp_latest:
                    installed_text += " ✓"
                
                self.exp_latest_label.configure(
                    text=latest_text,
                    text_color=("yellow" if not is_exp_latest else "white")
                )
                self.exp_installed_label.configure(
                    text=installed_text,
                    text_color="green" if is_exp_latest else "white"
                )
                
                # Check stable version
                stable_response = requests.get("https://api.github.com/repos/CleverRaven/Cataclysm-DDA/releases/latest")
                stable_info = json.loads(stable_response.text)
                self.latest_stable_tag = stable_info['tag_name']
                
                # Store stable patch notes
                self.stable_patch_notes = stable_info.get("body", "No patch notes available")
                
                # Find Mac OS X stable build with tiles
                self.latest_stable_url = None
                for asset in stable_info["assets"]:
                    name = asset["name"].lower()
                    if "osx" in name and "graphics" in name and "universal" in name and name.endswith(".dmg"):
                        self.latest_stable_url = asset["browser_download_url"]
                        break

                # Check Bright Nights version
                bn_response = requests.get("https://api.github.com/repos/cataclysmbnteam/Cataclysm-BN/releases")
                bn_releases = json.loads(bn_response.text)
                
                # Get the latest experimental release (first one in the list)
                if bn_releases:
                    bn_info = bn_releases[0]  # Latest release
                    self.latest_bn_tag = bn_info['tag_name']
                    
                    # Store BN patch notes
                    self.bn_patch_notes = bn_info.get("body", "No patch notes available")
                    if not self.showing_cdda:
                        self.patch_notes.delete("0.0", "end")
                        self.patch_notes.insert("0.0", self.bn_patch_notes)
                    
                    # Find Mac OS X BN build with tiles
                    self.latest_bn_url = None
                    for asset in bn_info["assets"]:
                        name = asset["name"].lower()
                        if "osx" in name and ("tiles" in name or "graphics" in name) and name.endswith(".dmg"):
                            self.latest_bn_url = asset["browser_download_url"]
                            break
                
                # Update patch notes display based on current view
                if self.showing_cdda:
                    if self.showing_experimental_notes:
                        self.patch_notes.delete("0.0", "end")
                        self.patch_notes.insert("0.0", self.experimental_patch_notes)
                    else:
                        self.patch_notes.delete("0.0", "end")
                        self.patch_notes.insert("0.0", self.stable_patch_notes)
                
                # Check DCSS version
                dcss_response = requests.get("https://api.github.com/repos/crawl/crawl/releases/latest")
                dcss_info = json.loads(dcss_response.text)
                self.latest_dcss_tag = dcss_info['tag_name']
                self.dcss_patch_notes = dcss_info.get("body", "No patch notes available")
                
                # Find Mac OS X DCSS build
                self.latest_dcss_url = None
                for asset in dcss_info["assets"]:
                    name = asset["name"].lower()
                    if "mac" in name or "osx" in name or "darwin" in name:
                        self.latest_dcss_url = asset["browser_download_url"]
                        break
                
                # Update DCSS version display
                dcss_version = self.get_version(self.dcss_path, self.installed_dcss_version)
                is_dcss_latest = dcss_version == self.latest_dcss_tag
                
                latest_text = f"Latest:        {self.latest_dcss_tag}"
                installed_text = f"Installed:     {dcss_version if dcss_version else 'Not installed'}"
                if dcss_version and is_dcss_latest:
                    installed_text += " ✓"
                
                self.dcss_latest_label.configure(
                    text=latest_text,
                    text_color=("yellow" if not is_dcss_latest else "white")
                )
                
                # Update patch notes display based on current view
                if not self.showing_cdda:
                    if hasattr(self, 'dcss_frame') and not self.dcss_frame.winfo_ismapped():
                        if self.showing_experimental_notes:
                            self.patch_notes.delete("0.0", "end")
                            self.patch_notes.insert("0.0", self.experimental_patch_notes)
                        else:
                            self.patch_notes.delete("0.0", "end")
                            self.patch_notes.insert("0.0", self.stable_patch_notes)
                
                self.check_installed_versions()
                
            except Exception as e:
                self.status_text.set(f"Error checking versions: {str(e)}")
                print(f"Detailed error: {str(e)}")  # For debugging
        
        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()

    def download_version(self, version_type):
        if version_type == "experimental":
            if not self.latest_experimental_url:
                if self.latest_experimental_tag != self.latest_experimental_mac_tag:
                    self.status_text.set(f"No Mac build yet for {self.latest_experimental_tag}. Latest Mac build: {self.latest_experimental_mac_tag}")
                else:
                    self.status_text.set(f"No Mac download found for {version_type} version")
                return
            url = self.latest_experimental_url
            version_tag = self.latest_experimental_mac_tag
        elif version_type == "stable":
            url = self.latest_stable_url
            version_tag = self.latest_stable_tag
        elif version_type == "dcss":
            url = self.latest_dcss_url
            version_tag = self.latest_dcss_tag
            path = self.dcss_path
        else:  # bn
            url = self.latest_bn_url
            version_tag = self.latest_bn_tag
            path = self.bn_path
        
        if not url:
            self.status_text.set(f"No Mac download found for {version_type} version")
            return
        
        def download():
            try:
                self.status_text.set(f"Downloading {version_type} version...")
                
                # Create temporary directory for download
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Download file
                    response = requests.get(url, stream=True)
                    total_size = int(response.headers.get('content-length', 0))
                    
                    dmg_path = os.path.join(temp_dir, os.path.basename(urlparse(url).path))
                    
                    with open(dmg_path, 'wb') as f:
                        downloaded = 0
                        for data in response.iter_content(chunk_size=4096):
                            downloaded += len(data)
                            f.write(data)
                            progress = downloaded / total_size
                            self.progress_bar.set(progress)
                    
                    self.status_text.set("Mounting DMG...")
                    
                    # Mount the DMG
                    mount_process = subprocess.Popen(["hdiutil", "attach", dmg_path, "-nobrowse"], 
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, error = mount_process.communicate()
                    
                    if mount_process.returncode != 0:
                        raise Exception(f"Failed to mount DMG: {error.decode()}")
                    
                    # Find the mount point
                    mount_point = None
                    for line in output.decode().split('\n'):
                        if '/Volumes/' in line:
                            mount_point = line.split('\t')[-1].strip()
                            break
                    
                    if not mount_point:
                        raise Exception("Could not find DMG mount point")
                    
                    # Find the .app in the mounted DMG
                    app_name = None
                    for item in os.listdir(mount_point):
                        if item.endswith('.app'):
                            app_name = item
                            break
                    
                    if not app_name:
                        raise Exception("Could not find .app in mounted DMG")
                    
                    # Clear existing installation
                    if os.path.exists(path):
                        self.status_text.set("Removing old version...")
                        shutil.rmtree(path, ignore_errors=True)
                    os.makedirs(path, exist_ok=True)
                    
                    # Copy the .app
                    self.status_text.set("Installing new version...")
                    source_app = os.path.join(mount_point, app_name)
                    target_app = os.path.join(path, app_name)
                    shutil.copytree(source_app, target_app, symlinks=True)
                    
                    # Unmount the DMG
                    self.status_text.set("Cleaning up...")
                    subprocess.run(["hdiutil", "detach", mount_point], check=True)
                    
                    self.status_text.set(f"{version_type.capitalize()} version installed successfully!")
                    self.progress_bar.set(1)
                    
                    # Update tracked version after successful installation
                    if version_type == "dcss":
                        self.installed_dcss_version = version_tag
                    elif version_type == "experimental":
                        self.installed_experimental_version = version_tag
                    elif version_type == "stable":
                        self.installed_stable_version = version_tag
                    else:  # bn
                        self.installed_bn_version = version_tag
                    
                    # Save versions after successful installation
                    self.save_versions()
                    
                    self.check_installed_versions()
                    
            except Exception as e:
                self.status_text.set(f"Error during download: {str(e)}")
                self.progress_bar.set(0)
                print(f"Detailed error: {str(e)}")  # For debugging
        
        thread = threading.Thread(target=download)
        thread.daemon = True
        thread.start()

    def launch_game(self, version_type):
        path = self.experimental_path if version_type == "experimental" else self.stable_path
        
        if not os.path.exists(path):
            self.status_text.set(f"No {version_type} version installed")
            return
        
        app_paths = [f for f in os.listdir(path) if f.endswith(".app")]
        if not app_paths:
            self.status_text.set(f"No .app found in {version_type} folder")
            return
        
        app_path = os.path.join(path, app_paths[0])
        subprocess.Popen(["open", app_path])
        self.status_text.set(f"Launching {version_type} version...")

    def open_folder(self, version_type):
        if version_type == "experimental":
            path = self.experimental_path
        elif version_type == "stable":
            path = self.stable_path
        elif version_type == "dcss":
            path = self.dcss_path
        else:  # bn
            path = self.bn_path
        subprocess.Popen(["open", path])

    def on_closing(self):
        self.single_instance.cleanup()
        self.quit()

    def open_github_notes(self):
        if self.showing_cdda:
            base_url = "https://github.com/CleverRaven/Cataclysm-DDA/releases"
            if self.showing_experimental_notes:
                if self.latest_experimental_tag:
                    url = f"{base_url}/tag/{self.latest_experimental_tag}"
                else:
                    url = base_url
            else:
                if self.latest_stable_tag:
                    url = f"{base_url}/tag/{self.latest_stable_tag}"
                else:
                    url = f"{base_url}/latest"
        elif hasattr(self, 'dcss_frame') and self.dcss_frame.winfo_ismapped():
            # For DCSS
            if self.latest_dcss_tag:
                url = f"https://github.com/crawl/crawl/releases/tag/{self.latest_dcss_tag}"
            else:
                url = "https://github.com/crawl/crawl/releases"
        else:
            # For Bright Nights
            if self.latest_bn_tag:
                url = f"https://github.com/cataclysmbnteam/Cataclysm-BN/releases/tag/{self.latest_bn_tag}"
            else:
                url = "https://github.com/cataclysmbnteam/Cataclysm-BN/releases"
        
        webbrowser.open(url)

    def play_dcss_online(self):
        webbrowser.open("https://crawl.akrasiac.org:8443/#lobby")

    def _create_status_frame(self):
        # Progress bar and status in a separate frame
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=(5,2), sticky="ew")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(status_frame, textvariable=self.status_text)
        self.status_label.grid(row=1, column=0, padx=10, pady=(2,5), sticky="ew")

    def _create_patch_notes_frame(self):
        # Patch Notes Frame
        self.patch_frame = ctk.CTkFrame(self)
        self.patch_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        self.patch_frame.grid_columnconfigure(0, weight=1)
        self.patch_frame.grid_rowconfigure(1, weight=1)
        
        # Header frame for patch notes
        notes_header_frame = ctk.CTkFrame(self.patch_frame, fg_color="transparent")
        notes_header_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        notes_header_frame.grid_columnconfigure(1, weight=1)
        
        self.patch_notes_label = ctk.CTkLabel(notes_header_frame, 
                                            text="Latest Experimental Patch Notes:", 
                                            font=ctk.CTkFont(weight="bold"))
        self.patch_notes_label.grid(row=0, column=0, padx=5, sticky="w")
        
        button_frame = ctk.CTkFrame(notes_header_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, padx=5, sticky="e")
        
        self.toggle_button = ctk.CTkButton(button_frame,
                                         text="View Stable Notes",
                                         command=self.toggle_patch_notes,
                                         width=100,
                                         height=28)
        self.toggle_button.pack(side="left", padx=(0, 5))
        
        self.github_button = ctk.CTkButton(button_frame,
                                         text="View on Github",
                                         command=self.open_github_notes,
                                         width=100,
                                         height=28)
        self.github_button.pack(side="left")
        
        self.patch_notes = ctk.CTkTextbox(self.patch_frame, wrap="word")
        self.patch_notes.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        
        # Add variables for patch notes state
        self.showing_experimental_notes = True
        self.stable_patch_notes = ""
        self.experimental_patch_notes = ""
        self.bn_patch_notes = ""
        self.dcss_patch_notes = ""

if __name__ == "__main__":
    app = CDDALauncher()
    app.mainloop() 
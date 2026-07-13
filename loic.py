#!/usr/bin/env python3
# LOIC Installer for Termux (Android)
# Adapted from original script

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# Constants
GIT_REPO = "https://github.com/NewEraCracker/LOIC.git"
GIT_BRANCH = "master"

# Termux paths
HOME = Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
LOIC_DIR = HOME / "LOIC"
SRC_DIR = LOIC_DIR / "src"
EXE_PATH = SRC_DIR / "bin" / "Debug" / "LOIC.exe"
CONFIG_PATH = SRC_DIR / "bin" / "Debug" / "LOIC.exe.config"
APP_CONFIG_PATH = SRC_DIR / "app.config"

def run_command(cmd, check=False, capture=False):
    """Run a shell command"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        else:
            subprocess.run(cmd, shell=True, check=False)
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def which(command):
    """Check if command exists"""
    return shutil.which(command) is not None

def detect_termux():
    """Check if running in Termux"""
    return "com.termux" in os.environ.get("PREFIX", "")

def check_dependencies():
    """Check and install dependencies for Termux"""
    print("Checking dependencies for Termux...")
    
    # Install required packages
    packages = ["git", "mono", "msbuild"]
    for pkg in packages:
        if not which(pkg):
            print(f"Installing {pkg}...")
            run_command(f"pkg install -y {pkg}")
    
    # Check for xbuild (might be needed instead of msbuild)
    if not which("msbuild") and not which("xbuild"):
        print("Installing mono-msbuild...")
        run_command("pkg install -y mono-msbuild")
    
    print("Dependencies check complete.")

def is_loic():
    """Check if LOIC repository exists"""
    if LOIC_DIR.exists() and (LOIC_DIR / ".git").exists():
        try:
            result = run_command("git config --local --get remote.origin.url", capture=True)
            return result and "LOIC" in result
        except:
            return False
    return False

def get_loic():
    """Clone LOIC repository"""
    if not which("git"):
        print("Installing git...")
        run_command("pkg install -y git")
    
    if not is_loic():
        print(f"Cloning LOIC from {GIT_REPO}...")
        run_command(f"git clone {GIT_REPO} -b {GIT_BRANCH}")
    else:
        print("LOIC already exists.")

def compile_loic():
    """Compile LOIC for Termux"""
    get_loic()
    
    if not is_loic():
        print("Error: LOIC repository not found.")
        return False
    
    # Try msbuild first, fallback to xbuild
    build_tool = None
    if which("msbuild"):
        build_tool = "msbuild"
    elif which("xbuild"):
        build_tool = "xbuild"
    else:
        print("Error: Neither msbuild nor xbuild found.")
        print("Installing msbuild...")
        run_command("pkg install -y mono-msbuild")
        if which("msbuild"):
            build_tool = "msbuild"
        else:
            return False
    
    print(f"Compiling LOIC using {build_tool}...")
    os.chdir(SRC_DIR)
    
    # Try different build commands
    build_commands = [
        f"{build_tool} /p:TargetFrameworkVersion='v4.0'",
        f"{build_tool} /p:Configuration=Debug",
        f"{build_tool}",
    ]
    
    success = False
    for cmd in build_commands:
        print(f"Trying: {cmd}")
        result = run_command(cmd)
        if EXE_PATH.exists():
            success = True
            break
    
    os.chdir(HOME)
    
    if success:
        print("Compilation successful!")
        return True
    else:
        print("Compilation failed. Trying alternative method...")
        return compile_loic_alternative()

def compile_loic_alternative():
    """Alternative compilation method for Termux"""
    print("Attempting alternative compilation...")
    
    # Try using dmcs directly
    cs_files = list(SRC_DIR.glob("**/*.cs"))
    if not cs_files:
        print("No C# files found.")
        return False
    
    # Compile all CS files directly
    references = [
        "System.dll",
        "System.Windows.Forms.dll",
        "System.Drawing.dll",
        "System.Net.dll",
        "System.Xml.dll"
    ]
    
    ref_args = " ".join([f"-r:{ref}" for ref in references])
    output = str(EXE_PATH)
    
    os.chdir(SRC_DIR)
    cmd = f"dmcs -target:winexe -out:{output} {ref_args} {SRC_DIR}/**/*.cs"
    print(f"Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    os.chdir(HOME)
    
    if EXE_PATH.exists():
        print("Alternative compilation successful!")
        return True
    else:
        print("Alternative compilation failed.")
        print("Error output:", result.stderr)
        return False

def run_loic():
    """Run LOIC application"""
    if not which("mono"):
        print("Mono not found. Installing...")
        run_command("pkg install -y mono")
    
    if not is_loic():
        print("LOIC not found. Cloning...")
        get_loic()
        compile_loic()
    
    if not EXE_PATH.exists():
        print("LOIC executable not found. Compiling...")
        compile_loic()
    
    if not EXE_PATH.exists():
        print("Error: Could not compile LOIC.")
        print("Checking for pre-compiled version...")
        check_precompiled()
        return
    
    # Copy config file if needed
    if APP_CONFIG_PATH.exists() and not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(APP_CONFIG_PATH, CONFIG_PATH)
        print(f"Copied config to {CONFIG_PATH}")
    
    print("Running LOIC...")
    print("Note: LOIC may have limited functionality in Termux.")
    print("Press Ctrl+C to stop.")
    
    os.chdir(EXE_PATH.parent)
    try:
        # Try different mono runtime versions
        run_commands = [
            "mono --runtime=v4.0.30319 LOIC.exe",
            "mono LOIC.exe"
        ]
        
        for cmd in run_commands:
            print(f"Trying: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode == 0:
                break
    except KeyboardInterrupt:
        print("\nLOIC stopped.")
    finally:
        os.chdir(HOME)

def check_precompiled():
    """Check if there's a pre-compiled version available"""
    # Try to find any .exe file in the repository
    exe_files = list(LOIC_DIR.glob("**/*.exe"))
    if exe_files:
        print(f"Found pre-compiled executable: {exe_files[0]}")
        print("You can try running it manually with:")
        print(f"mono {exe_files[0]}")
    else:
        print("No pre-compiled executables found.")
        print("LOIC may not be compatible with Termux environment.")

def update_loic():
    """Update LOIC from repository"""
    if is_loic():
        print("Updating LOIC...")
        os.chdir(LOIC_DIR)
        run_command("git pull --rebase")
        os.chdir(HOME)
        compile_loic()
    else:
        print("Error: LOIC repository not found.")
        get_loic()
        compile_loic()

def print_usage():
    """Print usage information"""
    print("LOIC Installer for Termux")
    print("=" * 40)
    print()
    print("Usage: python3 loic.py <install|update|run>")
    print()
    print("Commands:")
    print("  install  - Install LOIC and dependencies")
    print("  update   - Update LOIC to latest version")
    print("  run      - Run LOIC application")
    print()
    print("Note: This script is optimized for Termux (Android)")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    
    if not detect_termux():
        print("Warning: Not running in Termux environment.")
        print("This script is optimized for Termux on Android.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        print("Installing LOIC for Termux...")
        check_dependencies()
        get_loic()
        compile_loic()
        if EXE_PATH.exists():
            print("Installation successful!")
            print("Run with: python3 loic.py run")
        else:
            print("Installation failed. Please check errors above.")
            
    elif command == "update":
        update_loic()
        
    elif command == "run":
        run_loic()
        
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()

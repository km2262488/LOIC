#!/usr/bin/env python3
# Copyfuck © 2010 q
# Edited by NewEraCracker
# Converted to Python by Assistant
#
# This script installs, updates and runs LOIC on Linux.
#
# Supported distributions:
#    * Ubuntu
#    * Debian
#    * Fedora
#
# Before using you must install monodevelop from:
# https://www.monodevelop.com/download/#fndtn-download-lin
#
# Usage: python3 loic.py <install|update|run>
#

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Constants
GIT_REPO = "https://github.com/NewEraCracker/LOIC.git"
GIT_BRANCH = "master"

DEB_MONO_PKG = "monodevelop liblog4net-cil-dev mono-devel mono-runtime-common mono-runtime libmono-system-windows-forms4.0-cil"
FED_MONO_PKG = "mono-basic mono-devel monodevelop mono-tools"

LOIC_DIR = Path("LOIC")
SRC_DIR = LOIC_DIR / "src"
EXE_PATH = SRC_DIR / "bin" / "Debug" / "LOIC.exe"
CONFIG_PATH = SRC_DIR / "bin" / "Debug" / "LOIC.exe.config"
APP_CONFIG_PATH = SRC_DIR / "app.config"

def lower(text):
    return text.lower()

def what_distro():
    """Detect Linux distribution"""
    try:
        # Check for Ubuntu/Debian
        for release_file in Path("/etc").glob("*-release"):
            content = release_file.read_text().lower()
            if "ubuntu" in content:
                return "ubuntu"
            elif "debian" in content:
                return "debian"
        
        # Check for Fedora
        if Path("/etc/fedora-release").exists():
            return "fedora"
        
        # Default to Debian-based
        return "debian"
        
    except Exception:
        return "debian"

DISTRO = what_distro()

def run_command(cmd, check=True, capture=False):
    """Run a shell command and return output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {cmd}")
        if hasattr(e, 'stderr'):
            print(e.stderr)
        return False if not check else None

def which(command):
    """Check if command exists"""
    return shutil.which(command) is not None

def ensure_git():
    """Install git if not present"""
    if not which("git"):
        print("Git not found. Installing...")
        if DISTRO in ["ubuntu", "debian"]:
            run_command("sudo apt-get update")
            run_command("sudo apt-get install -y git")
        elif DISTRO == "fedora":
            run_command("sudo yum install -y git")
        else:
            print("Unknown distribution. Please install git manually.")
            sys.exit(1)

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
    ensure_git()
    if not is_loic():
        print(f"Cloning LOIC from {GIT_REPO}...")
        run_command(f"git clone {GIT_REPO} -b {GIT_BRANCH}")

def install_mono_packages():
    """Install Mono development packages"""
    print(f"Installing Mono packages for {DISTRO}...")
    
    if DISTRO in ["ubuntu", "debian"]:
        run_command("sudo apt-get update")
        run_command(f"sudo apt-get install -y {DEB_MONO_PKG}")
    elif DISTRO == "fedora":
        run_command(f"sudo yum install -y {FED_MONO_PKG}")
    else:
        print("Unknown distribution. Please install Mono packages manually.")
        print(f"Required packages: {DEB_MONO_PKG if DISTRO in ['ubuntu', 'debian'] else FED_MONO_PKG}")
        sys.exit(1)

def compile_loic():
    """Compile LOIC"""
    get_loic()
    
    if not is_loic():
        print("Error: You are not in a LOIC repository.")
        sys.exit(1)
    
    install_mono_packages()
    
    print("Compiling LOIC...")
    os.chdir(SRC_DIR)
    try:
        run_command("xbuild /p:TargetFrameworkVersion='v4.0'")
    finally:
        os.chdir("..")  # Return to original directory

def install_mono_runtime():
    """Install Mono runtime if not present"""
    if not which("mono"):
        print("Mono runtime not found. Installing...")
        if DISTRO in ["ubuntu", "debian"]:
            run_command("sudo apt-get install -y mono-runtime")
        elif DISTRO == "fedora":
            run_command("sudo yum install -y mono-runtime")
        else:
            print("Please install mono-runtime manually.")
            sys.exit(1)

def run_loic():
    """Run LOIC application"""
    if not is_loic():
        print("LOIC not found. Installing...")
        compile_loic()
    
    if not EXE_PATH.exists():
        print("LOIC executable not found. Compiling...")
        compile_loic()
    
    install_mono_runtime()
    
    # Copy config file if it doesn't exist
    if APP_CONFIG_PATH.exists() and not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(APP_CONFIG_PATH, CONFIG_PATH)
        print(f"Copied config to {CONFIG_PATH}")
    
    print("Running LOIC...")
    os.chdir(EXE_PATH.parent)
    try:
        run_command("mono --runtime=v4.0.30319 LOIC.exe")
    finally:
        os.chdir("..")  # Return to original directory

def update_loic():
    """Update LOIC from repository"""
    ensure_git()
    
    if is_loic():
        print("Updating LOIC...")
        os.chdir(LOIC_DIR)
        try:
            run_command("git pull --rebase")
        finally:
            os.chdir("..")
        compile_loic()
    else:
        print("Error: You are not in a LOIC repository.")
        sys.exit(1)

def print_usage():
    """Print usage information"""
    print("Usage: python3 loic.py <install|update|run>")
    print()
    print("Commands:")
    print("  install  - Install LOIC and dependencies")
    print("  update   - Update LOIC to latest version")
    print("  run      - Run LOIC application")
    print()
    print("Supported distributions: Ubuntu, Debian, Fedora")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Check if running with sudo (for package installation)
    if command in ["install", "update"] and os.geteuid() != 0:
        print("Warning: This command may require sudo privileges for package installation.")
        print("If you encounter permission errors, run with sudo.")
    
    # Execute command
    if command == "install":
        compile_loic()
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
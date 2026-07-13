#!/usr/bin/env python3
# LOIC Installer for Termux (Android)
# Adapted for Termux environment

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Constants
GIT_REPO = "https://github.com/NewEraCracker/LOIC.git"
GIT_BRANCH = "master"

# Termux paths
HOME = Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
LOIC_BASE = HOME / "LOIC"

def find_loic_src():
    """Find the actual LOIC src directory"""
    possible_paths = [
        LOIC_BASE / "src",
        LOIC_BASE / "LOIC" / "src",
        LOIC_BASE / "LOIC" / "LOIC" / "src",
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "LOIC.sln").exists():
            return path
    return None

def find_exe_path(src_dir):
    """Find the LOIC executable path"""
    if src_dir is None:
        return None
    
    possible_exe = [
        src_dir / "bin" / "Debug" / "LOIC.exe",
        src_dir / "bin" / "Release" / "LOIC.exe",
        src_dir / "LOIC" / "bin" / "Debug" / "LOIC.exe",
        src_dir / "LOIC" / "bin" / "Release" / "LOIC.exe",
    ]
    
    for exe in possible_exe:
        if exe.exists():
            return exe
    return possible_exe[0]  # Return default path

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

def install_package(pkg):
    """Install package in Termux"""
    print(f"Installing {pkg}...")
    run_command(f"pkg install -y {pkg}")

def check_dependencies():
    """Check and install dependencies for Termux"""
    print("Checking dependencies for Termux...")
    
    # Update package list
    run_command("pkg update")
    
    # Install required packages
    packages = ["git", "mono", "msbuild", "mono-msbuild"]
    
    for pkg in packages:
        if not which(pkg):
            install_package(pkg)
    
    # Check if we have build tools
    if not which("msbuild") and not which("xbuild"):
        print("Installing mono-msbuild...")
        install_package("mono-msbuild")
        install_package("mono")
    
    print("Dependencies check complete.")

def is_loic():
    """Check if LOIC repository exists"""
    # Check both possible locations
    if (LOIC_BASE / ".git").exists():
        return True
    if (LOIC_BASE / "LOIC" / ".git").exists():
        return True
    return False

def get_loic():
    """Clone LOIC repository"""
    if not which("git"):
        install_package("git")
    
    if is_loic():
        print("LOIC already exists.")
        return
    
    print(f"Cloning LOIC from {GIT_REPO}...")
    os.chdir(HOME)
    run_command(f"git clone {GIT_REPO} -b {GIT_BRANCH}")
    
    # Check if cloned successfully
    if not is_loic():
        print("Error: Failed to clone LOIC repository.")
        return False
    
    # Find and show the structure
    src_dir = find_loic_src()
    if src_dir:
        print(f"Found LOIC source at: {src_dir}")
    else:
        print("Warning: LOIC source directory not found.")
    
    return True

def compile_loic():
    """Compile LOIC for Termux"""
    # Get LOIC first
    get_loic()
    
    # Find src directory
    src_dir = find_loic_src()
    if not src_dir:
        print("Error: Could not find LOIC source directory.")
        print("Looking in:", LOIC_BASE)
        print("Contents:", list(LOIC_BASE.glob("**/*.sln")))
        return False
    
    print(f"Compiling LOIC in: {src_dir}")
    os.chdir(src_dir.parent if src_dir.parent != src_dir else src_dir)
    
    # Try different build tools
    build_tools = []
    if which("msbuild"):
        build_tools.append("msbuild")
    if which("xbuild"):
        build_tools.append("xbuild")
    
    if not build_tools:
        print("Installing build tools...")
        install_package("mono-msbuild")
        if which("msbuild"):
            build_tools.append("msbuild")
        else:
            print("Error: No build tool available.")
            return False
    
    success = False
    for tool in build_tools:
        print(f"Trying {tool}...")
        
        # Try different build commands
        commands = [
            f"{tool} /p:TargetFrameworkVersion=v4.0 /p:Configuration=Debug",
            f"{tool} /p:Configuration=Debug",
            f"{tool} /p:TargetFrameworkVersion=v4.0",
            f"{tool}",
        ]
        
        for cmd in commands:
            print(f"  Running: {cmd}")
            run_command(cmd)
            
            # Check if exe was created
            exe_path = find_exe_path(src_dir)
            if exe_path and exe_path.exists():
                print(f"✅ Compilation successful! EXE found at: {exe_path}")
                success = True
                break
        
        if success:
            break
    
    if not success:
        print("❌ Compilation failed. Trying fallback method...")
        success = compile_loic_fallback(src_dir)
    
    return success

def compile_loic_fallback(src_dir):
    """Fallback compilation using mcs/dmcs directly"""
    print("Using fallback compilation method...")
    
    # Find all .cs files
    cs_files = list(src_dir.glob("**/*.cs"))
    if not cs_files:
        print("No .cs files found.")
        return False
    
    # Check for compiler
    compiler = None
    for cmd in ["dmcs", "mcs", "csc"]:
        if which(cmd):
            compiler = cmd
            break
    
    if not compiler:
        print("No C# compiler found.")
        return False
    
    # Compile all files
    output_path = src_dir / "LOIC.exe"
    refs = [
        "System.dll",
        "System.Windows.Forms.dll", 
        "System.Drawing.dll",
        "System.Net.dll",
        "System.Xml.dll"
    ]
    
    ref_args = " ".join([f"-r:{ref}" for ref in refs])
    cs_files_str = " ".join([str(f) for f in cs_files])
    
    cmd = f"{compiler} -target:winexe -out:{output_path} {ref_args} {cs_files_str}"
    print(f"Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if output_path.exists():
        print(f"✅ Fallback compilation successful! EXE at: {output_path}")
        return True
    else:
        print("❌ Fallback compilation failed.")
        print("Error:", result.stderr[:500])
        return False

def run_loic():
    """Run LOIC application"""
    if not which("mono"):
        print("Mono not found. Installing...")
        install_package("mono")
    
    # Find source and exe
    src_dir = find_loic_src()
    if not src_dir:
        print("LOIC not found. Installing...")
        get_loic()
        src_dir = find_loic_src()
        if not src_dir:
            print("Error: Could not find LOIC.")
            return
    
    exe_path = find_exe_path(src_dir)
    if not exe_path or not exe_path.exists():
        print("LOIC executable not found. Compiling...")
        if not compile_loic():
            print("Error: Compilation failed.")
            return
        exe_path = find_exe_path(src_dir)
    
    if not exe_path or not exe_path.exists():
        print("Error: Could not find LOIC executable.")
        return
    
    print(f"Running LOIC from: {exe_path}")
    os.chdir(exe_path.parent)
    
    # Copy config if needed
    config_src = src_dir / "app.config"
    config_dst = exe_path.parent / "LOIC.exe.config"
    if config_src.exists() and not config_dst.exists():
        shutil.copy2(config_src, config_dst)
        print(f"Copied config to {config_dst}")
    
    print("\n" + "="*50)
    print("Starting LOIC...")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    try:
        # Try with different mono runtime versions
        commands = [
            f"mono --runtime=v4.0.30319 {exe_path.name}",
            f"mono {exe_path.name}"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode == 0:
                break
            
    except KeyboardInterrupt:
        print("\n\nLOIC stopped.")
    except Exception as e:
        print(f"Error running LOIC: {e}")
    finally:
        os.chdir(HOME)

def update_loic():
    """Update LOIC from repository"""
    # Find the git repo
    git_dir = None
    if (LOIC_BASE / ".git").exists():
        git_dir = LOIC_BASE
    elif (LOIC_BASE / "LOIC" / ".git").exists():
        git_dir = LOIC_BASE / "LOIC"
    
    if git_dir:
        print(f"Updating LOIC at {git_dir}...")
        os.chdir(git_dir)
        run_command("git pull --rebase")
        os.chdir(HOME)
        compile_loic()
    else:
        print("LOIC repository not found. Cloning...")
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
        print("📦 Installing LOIC for Termux...")
        check_dependencies()
        if compile_loic():
            print("\n✅ Installation successful!")
            print("Run with: python3 loic.py run")
        else:
            print("\n❌ Installation failed.")
            print("Please check errors above.")
            print("You may need to install mono manually:")
            print("  pkg install mono mono-msbuild")
            
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

package main

import (
	"archive/zip"
	"bufio"
	"bytes"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

const (
	gitRepo   = "https://github.com/NewEraCracker/LOIC.git"
	gitBranch = "master"
)

var (
	homeDir    string
	loicDir    string
	osArch     string
)

func init() {
	// Get home directory
	home, err := os.UserHomeDir()
	if err != nil {
		fmt.Println("Error getting home directory:", err)
		os.Exit(1)
	}
	homeDir = home
	loicDir = filepath.Join(homeDir, "LOIC")
	
	// Get OS/Architecture
	osArch = runtime.GOOS + "/" + runtime.GOARCH
}

func main() {
	if len(os.Args) != 2 {
		printUsage()
		os.Exit(1)
	}

	command := strings.ToLower(os.Args[1])

	switch command {
	case "install":
		installLOIC()
	case "update":
		updateLOIC()
	case "run":
		runLOIC()
	default:
		fmt.Printf("Unknown command: %s\n", command)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Println("LOIC Installer for Linux/Termux")
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println()
	fmt.Println("Usage: go run loic.go <install|update|run>")
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  install  - Install LOIC and dependencies")
	fmt.Println("  update   - Update LOIC to latest version")
	fmt.Println("  run      - Run LOIC application")
	fmt.Println()
	fmt.Println("Note: This script is optimized for Linux and Termux")
}

func runCommand(cmd string, args ...string) (string, error) {
	var stdout, stderr bytes.Buffer
	
	command := exec.Command(cmd, args...)
	command.Stdout = &stdout
	command.Stderr = &stderr
	
	err := command.Run()
	if err != nil {
		return stdout.String(), fmt.Errorf("error running command: %v, stderr: %s", err, stderr.String())
	}
	
	return stdout.String(), nil
}

func runCommandShell(cmd string) (string, error) {
	var stdout, stderr bytes.Buffer
	
	command := exec.Command("bash", "-c", cmd)
	command.Stdout = &stdout
	command.Stderr = &stderr
	
	err := command.Run()
	if err != nil {
		return stdout.String(), fmt.Errorf("error running command: %v, stderr: %s", err, stderr.String())
	}
	
	return stdout.String(), nil
}

func which(command string) bool {
	_, err := exec.LookPath(command)
	return err == nil
}

func isTermux() bool {
	prefix := os.Getenv("PREFIX")
	return strings.Contains(prefix, "com.termux")
}

func checkDependencies() {
	fmt.Println("Checking dependencies...")
	
	if isTermux() {
		// Termux dependencies
		fmt.Println("Detected Termux environment")
		
		// Update packages
		fmt.Println("Updating package list...")
		runCommand("pkg", "update")
		
		// Install required packages
		packages := []string{"git", "mono"}
		for _, pkg := range packages {
			if !which(pkg) {
				fmt.Printf("Installing %s...\n", pkg)
				runCommand("pkg", "install", "-y", pkg)
			}
		}
	} else {
		// Linux dependencies
		fmt.Println("Detected Linux environment")
		
		// Detect distribution
		distro := detectDistro()
		fmt.Printf("Distribution: %s\n", distro)
		
		var packages []string
		var installCmd string
		
		switch distro {
		case "ubuntu", "debian":
			installCmd = "apt-get"
			packages = []string{
				"git",
				"mono-devel",
				"mono-runtime",
				"libmono-system-windows-forms4.0-cil",
				"monodevelop",
			}
		case "fedora":
			installCmd = "dnf"
			packages = []string{
				"git",
				"mono-devel",
				"mono-tools",
				"mono-basic",
			}
		default:
			fmt.Println("Unknown distribution. Installing base packages...")
			if which("apt-get") {
				installCmd = "apt-get"
				packages = []string{"git", "mono-devel", "mono-runtime"}
			} else if which("dnf") {
				installCmd = "dnf"
				packages = []string{"git", "mono-devel", "mono-runtime"}
			} else {
				fmt.Println("Please install manually: git, mono")
				return
			}
		}
		
		// Install packages with sudo
		for _, pkg := range packages {
			if !which(pkg) && pkg != "monodevelop" && pkg != "mono-tools" {
				fmt.Printf("Installing %s...\n", pkg)
				runCommand("sudo", installCmd, "install", "-y", pkg)
			}
		}
	}
	
	fmt.Println("✅ Dependencies check complete")
}

func detectDistro() string {
	// Try to detect distribution
	releaseFiles := []string{
		"/etc/os-release",
		"/etc/lsb-release",
		"/etc/debian_version",
		"/etc/fedora-release",
	}
	
	for _, file := range releaseFiles {
		if _, err := os.Stat(file); err == nil {
			content, err := os.ReadFile(file)
			if err == nil {
				text := strings.ToLower(string(content))
				if strings.Contains(text, "ubuntu") {
					return "ubuntu"
				}
				if strings.Contains(text, "debian") {
					return "debian"
				}
				if strings.Contains(text, "fedora") {
					return "fedora"
				}
			}
		}
	}
	
	// Default to ubuntu
	return "ubuntu"
}

func isLOIC() bool {
	if _, err := os.Stat(filepath.Join(loicDir, ".git")); err == nil {
		return true
	}
	if _, err := os.Stat(filepath.Join(loicDir, "LOIC", ".git")); err == nil {
		return true
	}
	return false
}

func getLOIC() error {
	fmt.Println("Cloning LOIC repository...")
	
	if isLOIC() {
		fmt.Println("LOIC already exists.")
		return nil
	}
	
	// Try git clone
	cmd := fmt.Sprintf("git clone %s -b %s", gitRepo, gitBranch)
	if isTermux() {
		cmd = fmt.Sprintf("git clone %s -b %s", gitRepo, gitBranch)
	}
	
	_, err := runCommandShell(cmd)
	if err != nil {
		return fmt.Errorf("failed to clone repository: %v", err)
	}
	
	return nil
}

func findSrcDir() string {
	possiblePaths := []string{
		filepath.Join(loicDir, "src"),
		filepath.Join(loicDir, "LOIC", "src"),
		filepath.Join(loicDir, "LOIC", "LOIC", "src"),
	}
	
	for _, path := range possiblePaths {
		if _, err := os.Stat(filepath.Join(path, "LOIC.sln")); err == nil {
			return path
		}
	}
	
	return ""
}

func findExePath(srcDir string) string {
	if srcDir == "" {
		return ""
	}
	
	possibleExe := []string{
		filepath.Join(srcDir, "bin", "Debug", "LOIC.exe"),
		filepath.Join(srcDir, "bin", "Release", "LOIC.exe"),
		filepath.Join(srcDir, "LOIC.exe"),
	}
	
	for _, exe := range possibleExe {
		if _, err := os.Stat(exe); err == nil {
			return exe
		}
	}
	
	return possibleExe[0]
}

func compileLOIC() error {
	fmt.Println("Compiling LOIC...")
	
	if err := getLOIC(); err != nil {
		return err
	}
	
	srcDir := findSrcDir()
	if srcDir == "" {
		return fmt.Errorf("could not find LOIC source directory")
	}
	
	fmt.Printf("Source directory: %s\n", srcDir)
	
	// Change to src directory
	originalDir, _ := os.Getwd()
	defer os.Chdir(originalDir)
	
	if err := os.Chdir(srcDir); err != nil {
		return fmt.Errorf("failed to change directory: %v", err)
	}
	
	// Try different compilation methods
	compileMethods := []struct {
		name    string
		command string
	}{
		{"MSBuild", "msbuild /p:TargetFrameworkVersion=v4.0 /p:Configuration=Debug"},
		{"XBuild", "xbuild /p:TargetFrameworkVersion=v4.0"},
		{"MCS/Direct", "mcs -target:winexe -out:LOIC.exe *.cs -r:System.Windows.Forms.dll -r:System.dll -r:System.Drawing.dll"},
	}
	
	for _, method := range compileMethods {
		fmt.Printf("Trying: %s\n", method.name)
		
		// Split command
		parts := strings.Fields(method.command)
		if len(parts) == 0 {
			continue
		}
		
		cmd := parts[0]
		args := parts[1:]
		
		if which(cmd) {
			_, err := runCommand(cmd, args...)
			if err == nil {
				// Check if executable was created
				exePath := findExePath(srcDir)
				if _, err := os.Stat(exePath); err == nil {
					fmt.Printf("✅ Compilation successful! EXE: %s\n", exePath)
					return nil
				}
			}
		}
	}
	
	// Try direct compilation with mcs on all .cs files
	fmt.Println("Trying full compilation with mcs...")
	
	// Find all .cs files
	pattern := "*.cs"
	matches, err := filepath.Glob(filepath.Join(srcDir, "**", pattern))
	if err == nil && len(matches) > 0 {
		var csFiles []string
		for _, match := range matches {
			if !strings.Contains(match, "bin") && !strings.Contains(match, "obj") {
				csFiles = append(csFiles, match)
			}
		}
		
		if len(csFiles) > 0 {
			args := []string{
				"-target:winexe",
				"-out:LOIC.exe",
				"-r:System.Windows.Forms.dll",
				"-r:System.dll",
				"-r:System.Drawing.dll",
				"-r:System.Net.dll",
				"-r:System.Xml.dll",
			}
			args = append(args, csFiles...)
			
			_, err := runCommand("mcs", args...)
			if err == nil {
				exePath := filepath.Join(srcDir, "LOIC.exe")
				if _, err := os.Stat(exePath); err == nil {
					fmt.Printf("✅ Compilation successful! EXE: %s\n", exePath)
					return nil
				}
			}
		}
	}
	
	return fmt.Errorf("all compilation methods failed")
}

func downloadLOICZip() error {
	fmt.Println("Downloading pre-compiled LOIC...")
	
	// Try to get latest release
	url := "https://github.com/NewEraCracker/LOIC/releases/latest/download/LOIC.zip"
	zipPath := filepath.Join(homeDir, "LOIC.zip")
	
	// Download
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("download failed: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("download failed with status: %s", resp.Status)
	}
	
	// Create file
	out, err := os.Create(zipPath)
	if err != nil {
		return err
	}
	defer out.Close()
	
	// Copy data
	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return err
	}
	
	fmt.Printf("Downloaded to: %s\n", zipPath)
	
	// Extract
	fmt.Println("Extracting...")
	os.MkdirAll(loicDir, 0755)
	
	reader, err := zip.OpenReader(zipPath)
	if err != nil {
		return err
	}
	defer reader.Close()
	
	for _, file := range reader.File {
		path := filepath.Join(loicDir, file.Name)
		
		if file.FileInfo().IsDir() {
			os.MkdirAll(path, 0755)
			continue
		}
		
		dir := filepath.Dir(path)
		os.MkdirAll(dir, 0755)
		
		src, err := file.Open()
		if err != nil {
			continue
		}
		defer src.Close()
		
		dst, err := os.Create(path)
		if err != nil {
			continue
		}
		defer dst.Close()
		
		io.Copy(dst, src)
	}
	
	// Clean up
	os.Remove(zipPath)
	fmt.Println("✅ Extraction complete")
	
	return nil
}

func installLOIC() {
	fmt.Println("📦 Installing LOIC...")
	
	checkDependencies()
	
	// Try different installation methods
	methods := []struct {
		name string
		fn   func() error
	}{
		{"Download pre-compiled", downloadLOICZip},
		{"Build from source", compileLOIC},
	}
	
	for _, method := range methods {
		fmt.Printf("\n🔧 Trying: %s\n", method.name)
		if err := method.fn(); err == nil {
			// Check if we have an executable
			exe := findExePath(findSrcDir())
			if _, err := os.Stat(exe); err == nil {
				fmt.Printf("\n✅ Installation successful!\n")
				fmt.Printf("📁 LOIC installed at: %s\n", loicDir)
				fmt.Printf("📄 Executable: %s\n", exe)
				fmt.Printf("\nRun with: go run loic.go run\n")
				return
			} else {
				fmt.Println("⚠️  Installation completed but no executable found")
			}
		} else {
			fmt.Printf("❌ Method failed: %v\n", err)
		}
	}
	
	fmt.Println("\n❌ All installation methods failed")
	fmt.Println("\nManual installation steps:")
	fmt.Println("1. Install mono: pkg install mono (Termux) or apt-get install mono-devel (Linux)")
	fmt.Println("2. Clone repository: git clone https://github.com/NewEraCracker/LOIC.git")
	fmt.Println("3. Try compiling: cd LOIC/src && mcs -target:winexe -out:LOIC.exe *.cs -r:System.Windows.Forms.dll")
}

func runLOIC() {
	fmt.Println("Running LOIC...")
	
	// Check if mono exists
	if !which("mono") {
		fmt.Println("❌ Mono not found. Please install mono first.")
		if isTermux() {
			fmt.Println("  pkg install mono")
		} else {
			fmt.Println("  sudo apt-get install mono-runtime (Ubuntu/Debian)")
			fmt.Println("  sudo dnf install mono-runtime (Fedora)")
		}
		return
	}
	
	// Find executable
	srcDir := findSrcDir()
	if srcDir == "" {
		fmt.Println("❌ LOIC source directory not found.")
		fmt.Println("Please run 'install' first: go run loic.go install")
		return
	}
	
	exePath := findExePath(srcDir)
	if _, err := os.Stat(exePath); err != nil {
		fmt.Println("❌ LOIC executable not found.")
		fmt.Println("Please run 'install' first: go run loic.go install")
		return
	}
	
	fmt.Printf("Executable: %s\n", exePath)
	
	// Change to executable directory
	exeDir := filepath.Dir(exePath)
	os.Chdir(exeDir)
	
	fmt.Println("\n" + strings.Repeat("=", 50))
	fmt.Println("LOIC is starting...")
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println(strings.Repeat("=", 50) + "\n")
	
	// Try different mono runtime versions
	commands := [][]string{
		{"mono", "--runtime=v4.0.30319", filepath.Base(exePath)},
		{"mono", filepath.Base(exePath)},
	}
	
	for _, cmd := range commands {
		fmt.Printf("Running: %s\n", strings.Join(cmd, " "))
		execCmd := exec.Command(cmd[0], cmd[1:]...)
		execCmd.Stdout = os.Stdout
		execCmd.Stderr = os.Stderr
		
		if err := execCmd.Run(); err == nil {
			break
		}
	}
	
	// Return to original directory
	os.Chdir(homeDir)
}

func updateLOIC() {
	fmt.Println("Updating LOIC...")
	
	if isLOIC() {
		if _, err := os.Stat(filepath.Join(loicDir, ".git")); err == nil {
			fmt.Println("Pulling latest changes...")
			os.Chdir(loicDir)
			runCommand("git", "pull", "--rebase")
			os.Chdir(homeDir)
			
			fmt.Println("Recompiling...")
			compileLOIC()
			return
		}
	}
	
	fmt.Println("LOIC not found in git repository. Reinstalling...")
	os.RemoveAll(loicDir)
	installLOIC()
}

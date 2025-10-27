#!/bin/bash

# SOC Security Tools Installation Script
# This script downloads and installs security scanning tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$TOOLS_DIR"

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

if [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        PLATFORM="macOS_arm64"
        PLATFORM_ALT="darwin_arm64"
    else
        PLATFORM="macOS_amd64"
        PLATFORM_ALT="darwin_amd64"
    fi
elif [ "$OS" = "Linux" ]; then
    if [ "$ARCH" = "x86_64" ]; then
        PLATFORM="linux_amd64"
        PLATFORM_ALT="linux_amd64"
    else
        PLATFORM="linux_arm64"
        PLATFORM_ALT="linux_arm64"
    fi
else
    print_message "Unsupported operating system: $OS" "$RED"
    exit 1
fi

print_message "Detected platform: $PLATFORM" "$GREEN"

# Function to install Go tools
install_go_tool() {
    local tool_name=$1
    local github_repo=$2
    local version=$3

    print_message "Installing $tool_name..." "$YELLOW"

    local download_url="https://github.com/$github_repo/releases/download/$version/${tool_name}_${version#v}_${PLATFORM}.zip"

    cd "$TOOLS_DIR/$tool_name"
    curl -L -o "$tool_name.zip" "$download_url" 2>/dev/null || {
        # Try alternative naming
        download_url="https://github.com/$github_repo/releases/download/$version/${tool_name}_${version#v}_${PLATFORM_ALT}.zip"
        curl -L -o "$tool_name.zip" "$download_url" 2>/dev/null
    }

    if [ -f "$tool_name.zip" ]; then
        unzip -q -o "$tool_name.zip"
        rm "$tool_name.zip"
        chmod +x "$tool_name" 2>/dev/null || true
        print_message "✓ $tool_name installed" "$GREEN"
    else
        print_message "✗ Failed to install $tool_name" "$RED"
    fi

    cd "$TOOLS_DIR"
}

# Install ProjectDiscovery tools
print_message "\n=== Installing ProjectDiscovery Tools ===" "$GREEN"

# Nuclei - Already installed, just update templates
if [ -f "$TOOLS_DIR/nuclei/nuclei" ]; then
    print_message "Nuclei already installed, updating templates..." "$YELLOW"
    cd "$TOOLS_DIR/nuclei"
    ./nuclei -update-templates -silent
    print_message "✓ Nuclei templates updated" "$GREEN"
else
    install_go_tool "nuclei" "projectdiscovery/nuclei" "v3.3.7"
fi

# Subfinder - Subdomain discovery
install_go_tool "subfinder" "projectdiscovery/subfinder" "v2.6.8"

# HTTPx - HTTP toolkit
install_go_tool "httpx" "projectdiscovery/httpx" "v1.6.10"

# Naabu - Port scanner
install_go_tool "naabu" "projectdiscovery/naabu" "v2.3.3"

# Katana - Web crawler
install_go_tool "katana" "projectdiscovery/katana" "v1.1.1"

# Install Python-based tools
print_message "\n=== Installing Python Tools ===" "$GREEN"

# Create Python virtual environment for tools
if [ ! -d "$TOOLS_DIR/venv" ]; then
    print_message "Creating Python virtual environment..." "$YELLOW"
    python3 -m venv "$TOOLS_DIR/venv"
fi

source "$TOOLS_DIR/venv/bin/activate"

# Install Python packages
print_message "Installing Python security tools..." "$YELLOW"
pip install -q --upgrade pip
pip install -q \
    sqlmap \
    wafw00f \
    whatweb \
    fierce \
    dnsenum \
    theHarvester \
    sublist3r \
    dirsearch \
    paramspider \
    arjun \
    xsstrike \
    commix \
    2>/dev/null || true

print_message "✓ Python tools installed" "$GREEN"

# Download wordlists
print_message "\n=== Downloading Wordlists ===" "$GREEN"

cd "$TOOLS_DIR/wordlists"

# Common wordlist
if [ ! -f "common.txt" ]; then
    print_message "Downloading common wordlist..." "$YELLOW"
    curl -L -o common.txt "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt" 2>/dev/null
    print_message "✓ Common wordlist downloaded" "$GREEN"
fi

# Directory brute force wordlist
if [ ! -f "directory-list-2.3-medium.txt" ]; then
    print_message "Downloading directory wordlist..." "$YELLOW"
    curl -L -o directory-list-2.3-medium.txt "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-medium.txt" 2>/dev/null
    print_message "✓ Directory wordlist downloaded" "$GREEN"
fi

# Subdomain wordlist
if [ ! -f "subdomains-top1million-5000.txt" ]; then
    print_message "Downloading subdomain wordlist..." "$YELLOW"
    curl -L -o subdomains-top1million-5000.txt "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt" 2>/dev/null
    print_message "✓ Subdomain wordlist downloaded" "$GREEN"
fi

cd "$TOOLS_DIR"

# Create custom scanning scripts
print_message "\n=== Creating Custom Scripts ===" "$GREEN"

# Create subdomain enumeration script
cat > "$TOOLS_DIR/custom-scripts/subdomain_enum.sh" << 'EOF'
#!/bin/bash
domain=$1
output_dir=$2

mkdir -p "$output_dir"

# Run subfinder
../subfinder/subfinder -d "$domain" -o "$output_dir/subfinder.txt" -silent

# Run sublist3r
../venv/bin/python -m sublist3r -d "$domain" -o "$output_dir/sublist3r.txt" 2>/dev/null || true

# Combine and deduplicate
cat "$output_dir"/*.txt 2>/dev/null | sort -u > "$output_dir/all_subdomains.txt"

# Check live hosts
../httpx/httpx -l "$output_dir/all_subdomains.txt" -o "$output_dir/live_subdomains.txt" -silent

echo "Found $(wc -l < "$output_dir/all_subdomains.txt") unique subdomains"
echo "$(wc -l < "$output_dir/live_subdomains.txt") are live"
EOF

chmod +x "$TOOLS_DIR/custom-scripts/subdomain_enum.sh"

# Create port scanning script
cat > "$TOOLS_DIR/custom-scripts/port_scan.sh" << 'EOF'
#!/bin/bash
target=$1
output_dir=$2

mkdir -p "$output_dir"

# Fast port scan with naabu
../naabu/naabu -host "$target" -o "$output_dir/open_ports.txt" -silent

# Service detection with nmap (if installed)
if command -v nmap &> /dev/null; then
    ports=$(cat "$output_dir/open_ports.txt" | cut -d':' -f2 | tr '\n' ',' | sed 's/,$//')
    nmap -sV -p "$ports" "$target" -oN "$output_dir/nmap_services.txt" 2>/dev/null
fi

echo "Port scan completed for $target"
EOF

chmod +x "$TOOLS_DIR/custom-scripts/port_scan.sh"

# Create vulnerability scanning script
cat > "$TOOLS_DIR/custom-scripts/vuln_scan.sh" << 'EOF'
#!/bin/bash
target=$1
output_dir=$2

mkdir -p "$output_dir"

# Run Nuclei scan
../nuclei/nuclei -u "$target" -o "$output_dir/nuclei_results.txt" -silent

# Run specific scans based on technology
../nuclei/nuclei -u "$target" -tags cve,takeover,expose -o "$output_dir/critical_vulns.txt" -silent

echo "Vulnerability scan completed for $target"
EOF

chmod +x "$TOOLS_DIR/custom-scripts/vuln_scan.sh"

print_message "✓ Custom scripts created" "$GREEN"

# Create main configuration file
print_message "\n=== Creating Configuration ===" "$GREEN"

cat > "$TOOLS_DIR/configs/tools.conf" << EOF
# SOC Tools Configuration
TOOLS_DIR=$TOOLS_DIR
NUCLEI_BIN=$TOOLS_DIR/nuclei/nuclei
SUBFINDER_BIN=$TOOLS_DIR/subfinder/subfinder
HTTPX_BIN=$TOOLS_DIR/httpx/httpx
NAABU_BIN=$TOOLS_DIR/naabu/naabu
KATANA_BIN=$TOOLS_DIR/katana/katana
PYTHON_ENV=$TOOLS_DIR/venv/bin/python
WORDLISTS_DIR=$TOOLS_DIR/wordlists
CUSTOM_SCRIPTS_DIR=$TOOLS_DIR/custom-scripts
EOF

print_message "✓ Configuration created" "$GREEN"

# Summary
print_message "\n=== Installation Complete ===" "$GREEN"
print_message "Tools installed in: $TOOLS_DIR" "$YELLOW"
print_message "Configuration file: $TOOLS_DIR/configs/tools.conf" "$YELLOW"
print_message "\nTo use Python tools, activate the virtual environment:" "$YELLOW"
print_message "  source $TOOLS_DIR/venv/bin/activate" "$NC"

# Test installations
print_message "\n=== Testing Installations ===" "$GREEN"

if [ -f "$TOOLS_DIR/nuclei/nuclei" ]; then
    print_message "✓ Nuclei: $($TOOLS_DIR/nuclei/nuclei -version 2>&1 | head -1)" "$GREEN"
fi

if [ -f "$TOOLS_DIR/subfinder/subfinder" ]; then
    print_message "✓ Subfinder: Installed" "$GREEN"
fi

if [ -f "$TOOLS_DIR/httpx/httpx" ]; then
    print_message "✓ HTTPx: Installed" "$GREEN"
fi

if [ -f "$TOOLS_DIR/naabu/naabu" ]; then
    print_message "✓ Naabu: Installed" "$GREEN"
fi

if [ -f "$TOOLS_DIR/katana/katana" ]; then
    print_message "✓ Katana: Installed" "$GREEN"
fi

deactivate 2>/dev/null || true
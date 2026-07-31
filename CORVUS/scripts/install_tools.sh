#!/bin/bash

# Update system
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y golang git curl python3 python3-pip

# Install Go-based tools
echo "Installing Recon tools..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest

echo "Installing Vuln Scan tools..."
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/hahwul/dalfox/v2@latest

echo "Installing Fuzzing tools..."
go install -v github.com/ffuf/ffuf/v2@latest

# Add Go binaries to PATH
export PATH=$PATH:$(go env GOPATH)/bin
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc

# Python tools
pip3 install sqlmap

echo "Verifying installation..."
subfinder -version
nuclei -version
sqlmap --version

echo "Setup Complete!"

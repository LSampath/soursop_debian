#!/bin/bash

set -e
set -x

# Stop and disable the systemd service
sudo systemctl stop soursop || true
sudo systemctl disable soursop || true
sudo systemctl daemon-reload

# Remove the package
sudo dpkg -r python3-soursop || true

# Remove leftover files and systemd service
sudo rm -rf /var/log/soursop
sudo rm -rf /var/lib/soursop
sudo rm -rf /etc/soursop
sudo rm -f /lib/systemd/system/soursop.service

# Final daemon reload just to be safe
sudo systemctl daemon-reload

# Clear command cache
hash -r

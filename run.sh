#!/bin/bash

set -e      # immediately exit of any command fails
set -x      # print each command before running

# Clean previous builds
rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz

# Build .deb package
python3 setup.py --command-packages=stdeb.command bdist_deb

# Copy final .deb into root
sudo mv deb_dist/python3-soursop_*_all.deb soursop_0.1.deb

# Install the package
sudo dpkg -i soursop_0.1.deb

# Clean new build files
# comment out this line if you want to keep the build files
rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz

# Run systemd service
sudo systemctl daemon-reload
sudo systemctl enable soursop
sudo systemctl restart soursop
sudo systemctl status soursop --no-pager

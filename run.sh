#!/bin/bash

set -e
set -x

# Clean previous builds
rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz

# Build .deb package
python3 setup.py --command-packages=stdeb.command bdist_deb

# Install the package
sudo dpkg -i deb_dist/python3-soursop_0.1.0-1_all.deb

# Clean new build files
rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz

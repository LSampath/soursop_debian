#!/bin/bash

set -e      # immediately exit of any command fails
set -x      # print each command before running

# Clean previous builds
rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz temp_files soursop_*.deb

# Build .deb package
python3 setup.py --command-packages=stdeb.command bdist_deb

# extract deb file and replace the postinst file
mkdir -p temp_files
sudo cp deb_dist/python3-soursop_*_all.deb temp_files/soursop_temp.deb
sudo dpkg-deb -R temp_files/soursop_temp.deb temp_files/extracted_package
sudo cp postinst temp_files/extracted_package/DEBIAN/postinst
sudo dpkg-deb -b temp_files/extracted_package soursop_0.1.deb

# Install the package
sudo dpkg -i soursop_0.1.deb

# Clean new build files
sudo rm -rf dist deb_dist soursop.egg-info soursop-*.tar.gz temp_files

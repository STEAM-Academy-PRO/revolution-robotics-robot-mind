#!/bin/sh

setup_git() {
  git config --global user.email "travis@travis-ci.org"
  git config --global user.name "Travis CI"
}

prepare_firmware_files() {
  git clone https://github.com/RevolutionRobotics/RevvyFramework.git framework
  cd framework
  git checkout develop
  cd ..
  python3 -m tools.prepare --out=framework/data/firmware
  cd framework
  git add data/firmware
  git commit --message "Firmware update, Travis build: $TRAVIS_BUILD_NUMBER"
}

upload_files() {
  git remote add origin-fw https://${GH_TOKEN}@github.com/RevolutionRobotics/RevvyFramework.git > /dev/null 2>&1
  git push --quiet --set-upstream origin-fw develop
}

setup_git
prepare_firmware_files
upload_files

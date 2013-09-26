#!/bin/sh

if [ -d "deb_dist" ] && [ -d "rocket_depot.egg-info" ]; then
    echo 'cleaning previous build'
    rm -rf deb_dist rocket_depot.egg-info
fi

python setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist
dpkg-source -x rocket-depot_0.1-1ppa1-1.dsc
cd rocket-depot-0.1-1ppa1
debuild -S -sa

# dput ppa:robled/rocket-depot deb_dist/rocket-depot_0.1-1_source.changes

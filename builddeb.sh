#!/bin/sh

littlev=$(grep Debian-Version stdeb.cfg | awk {'print $2'})
bigv=$(grep version setup.py | awk {'print $3'} | cut -c 2-4)
echo $littlev
echo $bigv

if [ -d "deb_dist" ] && [ -d "rocket_depot.egg-info" ]; then
    echo 'cleaning previous build'
    rm -rf deb_dist rocket_depot.egg-info
fi

python setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist
dpkg-source -x rocket-depot_$bigv-$littlev.dsc
cd rocket-depot-$bigv
debuild -S -sa

echo 
echo 'To upload to PPA, copypasta:'
echo "dput ppa:robled/rocket-depot deb_dist/rocket-depot_"$bigv"-"$littlev"_source.changes"


#!/bin/bash

#littlev=$(grep Debian-Version stdeb.cfg | awk {'print $2'})
#bigv=$(grep version setup.py | awk {'print $3'} | cut -c 2-5)



build_dir='/tmp/rocket-depot_build'
rm -rf  "$build_dir"
mkdir -p "${build_dir}/build"
tar czf "${build_dir}/rocket-depot_1.0.0.orig.tar.gz" .
cd "${build_dir}/build"
tar xzf ../rocket-depot_1.0.0.orig.tar.gz
# Ubuntu wants -S for source packages only
debuild -S -krobled@electronsweatshop.com
cd ../
# debsign rocket-depot_1.0.0-1.0_source.changes
dpkg-source -x rocket-depot_1.0.0-1.0.dsc


# make switches for all this

echo
read -p "Upload to Ubuntu PPA? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pushd "$build_dir" && dput rocket-depot_trusty rocket-depot_1.0.0-1.0_source.changes; popd
fi

read -p "Upload to pypi? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pushd "$build_dir" && python setup.py sdist upload -r https://pypi.python.org/pypi --sign; popd
fi

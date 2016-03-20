#!/bin/bash -e

#littlev=$(grep Debian-Version stdeb.cfg | awk {'print $2'})
#bigv=$(grep version setup.py | awk {'print $3'} | cut -c 2-5)

export GPGKEY='1683174C'


build_dir='/tmp/rocket-depot_build'
rm -rf  "$build_dir"
mkdir -p "${build_dir}/build"
tar czf "${build_dir}/rocket-depot_1.0.0.orig.tar.gz" .
cd "${build_dir}/build"
tar xzf ../rocket-depot_1.0.0.orig.tar.gz
# Ubuntu wants -S for source packages only
debuild -S -k${GPGKEY}
debuild -b -us -uc -k${GPGKEY}
cd ../
# debsign rocket-depot_1.0.0-1.0_source.changes
dpkg-sig -p --sign builder rocket-depot_1.0.0-1.0_all.deb
# this might not be necessary
# dpkg-source -x rocket-depot_1.0.0-1.0.dsc -krobled@electronsweatshop.com
# fedora here, COPR doesn't care about signing
# rpmbuild -ba --sign rpmbuild/SPECS/rocket-depot.spec


# make switches for all this

echo
read -p "Upload to Ubuntu PPA? [y/n]" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pushd "$build_dir" && dput rocket-depot_trusty rocket-depot_1.0.0-1.0_source.changes; popd
fi

read -p "Upload to pypi? [y/n]" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pushd "$build_dir" && python setup.py sdist upload -r https://pypi.python.org/pypi --sign; popd
fi

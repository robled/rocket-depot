#!/bin/bash

littlev=$(grep Debian-Version stdeb.cfg | awk {'print $2'})
bigv=$(grep version setup.py | awk {'print $3'} | cut -c 2-5)
cleanlist=('deb_dist' 'rocket_depot.egg-info' 'dist' 'rocket-depot')

function clean {
    for i in "${cleanlist[@]}"
    do
        echo "cleaning $i if it exists"
        rm -rf $i
    done
}


function build {
    clean
    python setup.py --command-packages=stdeb.command sdist_dsc
    cd deb_dist
    dpkg-source -x rocket-depot_$bigv-$littlev.dsc
    cd rocket-depot-$bigv
    debuild -S -sa
    echo
    echo 'To upload to PPA/pypi, copypasta:'
    echo "dput ppa:robled/rocket-depot deb_dist/rocket-depot_"$bigv"-"$littlev"_source.changes"
    echo 'python setup.py sdist upload -r https://pypi.python.org/pypi --sign'
}


case "$1" in
        build)
            build
            ;;

        clean)
            clean
            ;;
        *)
            echo $"Usage: $0 {build|clean}"
            exit 1

esac

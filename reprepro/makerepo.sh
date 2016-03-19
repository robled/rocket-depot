#!/bin/bash -e

reprepro -Vb . includedeb jessie /tmp/rocket-depot_build/rocket-depot_1.0.0-1.0_all.deb

if [[ ! -f robled.gpg.key ]]; then
    gpg --armor --output robled.gpg.key --export 1683174C
fi


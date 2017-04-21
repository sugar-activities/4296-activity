#!/bin/sh
# Copyright (C) 2008, Vincent Povirk for CodeWeavers
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

ORIG_DIR=${PWD}
BUILD_DIR=$(mktemp -d)
WINE_ORIGIN=git://source.winehq.org/git/wine.git
WINE_BASE=wine-1.1.28
WINE_COMMIT=wine-1.1.28-30-gcc74d3d

mkdir "${BUILD_DIR}"/Wine.activity

cp -r app activity patches setup.py wineactivity.py filenames.py build.sh "${BUILD_DIR}"/Wine.activity

mkdir "${BUILD_DIR}"/Wine.activity/bin

cp bin/sugar-start-uri bin/sugar-run-from-journal "${BUILD_DIR}"/Wine.activity/bin

if test x = x"${WINE_TREE}"; then
    WINE_TREE="${BUILD_DIR}"/wine
fi

if test -e "${WINE_TREE}"/.git; then
    cd "${WINE_TREE}"
    
    if test x != x"${WINE_NEWTREE}"; then
        WINE_ORIGIN=$(git config remote.origin.url)
        WINE_BASE=$(git describe $(git merge-base HEAD origin/master))
        WINE_COMMIT=$(git describe HEAD)
        rm "${BUILD_DIR}"/Wine.activity/patches/*
        git format-patch -o "${BUILD_DIR}"/Wine.activity/patches "${WINE_BASE}" || exit 1
    fi
else
    git clone "${WINE_ORIGIN}" "${WINE_TREE}" || exit 1

    cd "${WINE_TREE}"

    git config user.email nobody@nowhere || exit 1
    git config user.name nobody || exit 1
fi

(git checkout "${WINE_COMMIT}" && test -z "$(git diff "${WINE_COMMIT}")") || \
    (git fetch && git checkout "${WINE_BASE}" && git am "${BUILD_DIR}"/Wine.activity/patches/*.patch && test -z "$(git diff)") || \
    exit 1

sed 's,^WINE_ORIGIN=.*$,WINE_ORIGIN='"${WINE_ORIGIN}"',' --in-place "${BUILD_DIR}"/Wine.activity/build.sh
sed 's,^WINE_BASE=.*$,WINE_BASE='"${WINE_BASE}"',' --in-place "${BUILD_DIR}"/Wine.activity/build.sh
sed 's,^WINE_COMMIT=.*$,WINE_COMMIT='"${WINE_COMMIT}"',' --in-place "${BUILD_DIR}"/Wine.activity/build.sh

./configure --prefix "${BUILD_DIR}"/Wine.activity ${CONFIG_OPTS:-CFLAGS=-Os} || exit 1
make ${MAKE_OPTS} || exit 1
make install-lib || exit 1

cd "${BUILD_DIR}"/Wine.activity

# winemenubuilder is needed on Linux to create freedesktop menus; it doesn't make sense on sugar
rm lib/wine/winemenubuilder.exe.so

if test x = x"${DEBUG}"; then
    find bin lib|xargs strip -g
fi

find . -type f | sed 's,^./,,g' > MANIFEST

./setup.py dist || exit 1

PACKAGE_FILENAME=*.xo

mv *.xo "${ORIG_DIR}" || exit 1

cd "${ORIG_DIR}"

rm -rf "${BUILD_DIR}"

echo Activity bundle created at ${ORIG_DIR}/${PACKAGE_FILENAME}


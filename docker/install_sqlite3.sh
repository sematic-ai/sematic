#!/bin/bash

wget https://www.sqlite.org/src/tarball/sqlite.tar.gz
tar xzf sqlite.tar.gz
pushd sqlite/

export CFLAGS="-DSQLITE_ENABLE_FTS3 \
    -DSQLITE_ENABLE_FTS3_PARENTHESIS \
    -DSQLITE_ENABLE_FTS4 \
    -DSQLITE_ENABLE_FTS5 \
    -DSQLITE_ENABLE_JSON1 \
    -DSQLITE_ENABLE_LOAD_EXTENSION \
    -DSQLITE_ENABLE_RTREE \
    -DSQLITE_ENABLE_STAT4 \
    -DSQLITE_ENABLE_UPDATE_DELETE_LIMIT \
    -DSQLITE_SOUNDEX \
    -DSQLITE_TEMP_STORE=3 \
    -DSQLITE_USE_URI \
    -O2 \
    -fPIC"

export PREFIX="/usr/local"

LIBS="-lm" ./configure --disable-tcl --enable-shared --enable-tempstore=always --prefix="$PREFIX"

make
make install

popd


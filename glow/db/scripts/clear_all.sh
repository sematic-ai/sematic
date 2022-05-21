#!/bin/sh
set -x

sqlite3 ~/.glow/db.sqlite3 < ${BUILD_WORKSPACE_DIRECTORY}/glow/db/scripts/clear_all.sql

#!/bin/bash
# Build script for Reporting-App JavaScript components. Uses Yarn and ParcelJS to compile JS components from src/ into
# modules in static/. Modules are configured to be served at the endpoint /static by Flask.

if [ $# -lt 1 ]
then
    echo "Usage: build_client.sh <yarn_toplevel>"
    exit 0
fi

cd $1

yarn install

js_targets="
src/bioinformatics_activity.js
"

parcel build $js_targets -d static --public-url /static

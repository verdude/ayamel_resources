#/bin/bash

if [ -z $(which unix2dos) ]; then
    echo "Install dos2unix"
    exit 1
fi
OIFS="$IFS"
IFS=$'\n'
for x in $(ls); do
    unix2dos $x
done


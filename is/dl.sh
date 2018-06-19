#!/bin/bash

set -e
folder=${1:-videos}
urls=${2:-brightcove_download_links.txt}

mkdir -p $folder

IFS=$'\n'
for x in $(cat $urls); do
    url=$(echo $x | python -c "import sys;print(sys.stdin.read().split('::')[0])")
    filename=$(echo $x | python -c "import sys;print(sys.stdin.read().split('::')[1])")
    echo "Downloading $url to: $folder/$filename"
    curl -s $url -o "$folder/$filename"
done


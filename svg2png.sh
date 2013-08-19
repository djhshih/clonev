#!/bin/bash

if [ $# -lt 1 ]; then
	echo "usage: $0 <file.svg>"
	exit
fi

input=$1
output=${input%.*}.png

inkscape -z --export-png $output --export-width 1200 --export-height 300 $input


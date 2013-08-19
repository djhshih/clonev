#!/bin/bash

if [ $# -lt 1 ]; then
	echo "usage: $0 <file.svg>"
	exit
fi

input=$1
output=${input%.*}.pdf

inkscape -z --export-pdf $output $input


#!/usr/bin/env sh

# usage: ./gen_mp4.sh <recording_dir> <output_file> [<num_segments>]

cat $1/segments.txt > $1/tmp.txt
if [ -z $3 ]
then
    tail -n $3 $1/segments.txt > $1/tmp.txt
fi
ffmpeg -f concat -i $1/tmp.txt -c copy $2

#! /bin/bash
#
# Invert, Clean, Restore. Generate an image from a single vis
# file.
#
# Usage: icr.sh [vis] [pol]
#
# where we select only the specified polarization. Output files are
#
# [vis].mp - Raw map
# [vis].bm - Beam
# [vis].cl - Cleaned map
# [vis].rm - Restored map

if [ x"$2" != xxx -a x"$2" != xyy ] ; then
    echo "Usage: %0 vis pol" 1>&2
    exit 1
fi

mp="$1".mp
bm="$1".bm
cl="$1".cl
rm="$1".rm

set -e -x

rm -rf $mp $bm $cl $rm
invert vis=$1 map=$mp beam=$bm select="-auto,pol($2)" options=double,mfs sup=0
clean map=$mp beam=$bm out=$cl niters=5000
restor map=$mp beam=$bm model=$cl out=$rm

#! /bin/bash
#
# Usage: avgim.sh
#
# Output files are
#
#
#
##################
# default params?
#imroot='j0332-0.1s'
#suffix='tst'
#phasebins=16
##################
imroot="$1"
suffix="$2"
timebins="$3"
imsize="$4"

#set -e -x   # for debugging
file='time-'${suffix}
cleansize=`echo 'scale=0; '${imsize}'/8' | bc`    # cleans in box +-cleansize

nsplit=`ls ${file}-time0a? | wc | gawk '{printf "%d \n", $0}' | head -n 1`
if [ $nsplit -eq 1 ]
then
    splitlist='aa'
elif [ $nsplit -eq 2 ]
then
    splitlist='aa ab'
elif [ $nsplit -eq 3 ]
then
    splitlist='aa ab ac'
elif [ $nsplit -eq 4 ]
then
    splitlist='aa ab ac ad'
elif [ $nsplit -eq 5 ]
then
    splitlist='aa ab ac ad ae'
elif [ $nsplit -eq 6 ]
then
    splitlist='aa ab ac ad ae af'
elif [ $nsplit -eq 7 ]
then
    splitlist='aa ab ac ad ae af ag'
elif [ $nsplit -eq 8 ]
then
    splitlist='aa ab ac ad ae af ag ah'
elif [ $nsplit -eq 9 ]
then
    splitlist='aa ab ac ad ae af ag ah ai'
elif [ $nsplit -eq 10 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj'
elif [ $nsplit -eq 11 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak'
elif [ $nsplit -eq 12 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al'
elif [ $nsplit -eq 13 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am'
elif [ $nsplit -eq 14 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an'
elif [ $nsplit -eq 15 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao'
elif [ $nsplit -eq 16 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap'
elif [ $nsplit -eq 17 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq'
elif [ $nsplit -eq 18 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar'
elif [ $nsplit -eq 19 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar as'
elif [ $nsplit -eq 20 ]
then
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as'
else
    echo 'Not getting split files higher than at!'
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as at'
fi

echo
echo '***Starting averaging of images across pols (and any split for miriad line limit)***'
echo

for ((i=0; i<=${timebins}-1; i++))
    do
    expmpxx=''
    expbmxx=''
    expmpyy=''
    expbmyy=''
    nsplit=0
    # average bm and mp across pols and splits (split for 256 line limit of miriad)
    for split in $splitlist
      do
      # generate short-named symbolic links for files
      ln -s ${imroot}-xx-${suffix}'-time'${i}${split}'.mp' ${i}${split}xm
      ln -s ${imroot}-xx-${suffix}'-time'${i}${split}'.bm' ${i}${split}xb
      ln -s ${imroot}-yy-${suffix}'-time'${i}${split}'.mp' ${i}${split}ym
      ln -s ${imroot}-yy-${suffix}'-time'${i}${split}'.bm' ${i}${split}yb

      expmpxx='+<'${i}${split}'xm>'${expmpxx}
      expbmxx='+<'${i}${split}'xb>'${expbmxx}
      expmpyy='+<'${i}${split}'ym>'${expmpyy}
      expbmyy='+<'${i}${split}'yb>'${expbmyy}
      nsplit=`echo ${nsplit}+1 | bc`

    done
    # need to use cut to remove superfluous + symbol
    expmpxx=`echo $expmpxx | cut -c2-`
    expbmxx=`echo $expbmxx | cut -c2-`
    expmpyy=`echo $expmpyy | cut -c2-`
    expbmyy=`echo $expbmyy | cut -c2-`

    # normalize by number of images
    expmpxx='('${expmpxx}')/'${nsplit}
    expbmxx='('${expbmxx}')/'${nsplit}
    expmpyy='('${expmpyy}')/'${nsplit}
    expbmyy='('${expbmyy}')/'${nsplit}

    maths exp=${expmpxx} out=${imroot}'-ixx-'${suffix}'-time'${i}'.mp'
    maths exp=${expbmxx} out=${imroot}'-ixx-'${suffix}'-time'${i}'.bm'
    maths exp=${expmpyy} out=${imroot}'-iyy-'${suffix}'-time'${i}'.mp'
    maths exp=${expbmyy} out=${imroot}'-iyy-'${suffix}'-time'${i}'.bm'
    maths exp='(<'${imroot}'-ixx-'${suffix}'-time'${i}'.mp>+<'${imroot}'-iyy-'${suffix}'-time'${i}'.mp>)/2' out=${imroot}'-i-'${suffix}'-time'${i}'.mp'
    maths exp='(<'${imroot}'-ixx-'${suffix}'-time'${i}'.bm>+<'${imroot}'-iyy-'${suffix}'-time'${i}'.bm>)/2' out=${imroot}'-i-'${suffix}'-time'${i}'.bm'
    maths exp='(<'${imroot}'-xx-'${suffix}'-avg'${i}'.mp>+<'${imroot}'-yy-'${suffix}'-avg'${i}'.mp>)/2' out=${imroot}'-i-'${suffix}'-avg'${i}'.mp'
    maths exp='(<'${imroot}'-xx-'${suffix}'-avg'${i}'.bm>+<'${imroot}'-yy-'${suffix}'-avg'${i}'.bm>)/2' out=${imroot}'-i-'${suffix}'-avg'${i}'.bm'

    # clean up temp files
    rm -rf ${imroot}'-ixx-'${suffix}'-time'${i}'.mp'
    rm -rf ${imroot}'-ixx-'${suffix}'-time'${i}'.bm'
    rm -rf ${imroot}'-iyy-'${suffix}'-time'${i}'.mp'
    rm -rf ${imroot}'-iyy-'${suffix}'-time'${i}'.bm'

    for split in $splitlist
    do
      rm ${i}${split}xm
      rm ${i}${split}xb
      rm ${i}${split}ym
      rm ${i}${split}yb
    done
done

# cat together along third axis  # only does up to 10 images for now.
if [ $timebins -gt 1 ] && [ $timebins -lt 100 ]
    then
    imcat in=${imroot}'-i-'${suffix}'-time*.mp' out=${imroot}'-itime-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time*.bm' out=${imroot}'-itime-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg*.mp' out=${imroot}'-iavg-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg*.bm' out=${imroot}'-iavg-'${suffix}'.bm' options=relax
elif [ $timebins -ge 100 ] && [ $timebins -lt 200 ]
    then
    imcat in=${imroot}'-i-'${suffix}'-time?.mp' out=${imroot}'-itime1-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time?.bm' out=${imroot}'-itime1-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg?.mp' out=${imroot}'-iavg1-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg?.bm' out=${imroot}'-iavg1-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time??.mp' out=${imroot}'-itime2-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time??.bm' out=${imroot}'-itime2-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg??.mp' out=${imroot}'-iavg2-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg??.bm' out=${imroot}'-iavg2-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time???.mp' out=${imroot}'-itime3-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time???.bm' out=${imroot}'-itime3-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg???.mp' out=${imroot}'-iavg3-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg???.bm' out=${imroot}'-iavg3-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-itime1-'${suffix}'.mp,'${imroot}'-itime2-'${suffix}'.mp,'${imroot}'-itime3-'${suffix}'.mp' out=${imroot}'-itime-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-itime1-'${suffix}'.bm,'${imroot}'-itime2-'${suffix}'.bm,'${imroot}'-itime3-'${suffix}'.bm' out=${imroot}'-itime-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-iavg1-'${suffix}'.mp,'${imroot}'-iavg2-'${suffix}'.mp,'${imroot}'-iavg3-'${suffix}'.mp' out=${imroot}'-iavg-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-iavg1-'${suffix}'.bm,'${imroot}'-iavg2-'${suffix}'.bm,'${imroot}'-iavg3-'${suffix}'.bm' out=${imroot}'-iavg-'${suffix}'.bm' options=relax
elif [ $timebins -ge 200 ]
    then
    imcat in=${imroot}'-i-'${suffix}'-time?.mp' out=${imroot}'-itime1-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time?.bm' out=${imroot}'-itime1-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg?.mp' out=${imroot}'-iavg1-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg?.bm' out=${imroot}'-iavg1-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time??.mp' out=${imroot}'-itime2-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time??.bm' out=${imroot}'-itime2-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg??.mp' out=${imroot}'-iavg2-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg??.bm' out=${imroot}'-iavg2-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time1??.mp' out=${imroot}'-itime3-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time1??.bm' out=${imroot}'-itime3-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg1??.mp' out=${imroot}'-iavg3-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg1??.bm' out=${imroot}'-iavg3-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time2??.mp' out=${imroot}'-itime4-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-time2??.bm' out=${imroot}'-itime4-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg2??.mp' out=${imroot}'-iavg4-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-i-'${suffix}'-avg2??.bm' out=${imroot}'-iavg4-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-itime1-'${suffix}'.mp,'${imroot}'-itime2-'${suffix}'.mp,'${imroot}'-itime3-'${suffix}'.mp,'${imroot}'-itime4-'${suffix}'.mp' out=${imroot}'-itime-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-itime1-'${suffix}'.bm,'${imroot}'-itime2-'${suffix}'.bm,'${imroot}'-itime3-'${suffix}'.bm,'${imroot}'-itime4-'${suffix}'.bm' out=${imroot}'-itime-'${suffix}'.bm' options=relax
    imcat in=${imroot}'-iavg1-'${suffix}'.mp,'${imroot}'-iavg2-'${suffix}'.mp,'${imroot}'-iavg3-'${suffix}'.mp,'${imroot}'-iavg4-'${suffix}'.mp' out=${imroot}'-iavg-'${suffix}'.mp' options=relax
    imcat in=${imroot}'-iavg1-'${suffix}'.bm,'${imroot}'-iavg2-'${suffix}'.bm,'${imroot}'-iavg3-'${suffix}'.bm,'${imroot}'-iavg4-'${suffix}'.bm' out=${imroot}'-iavg-'${suffix}'.bm' options=relax
    if [ $timebins -ge 300 ]
	then
	echo 'Note that timebins higher than 299 will not be in itime image cube'
    fi
elif [ $timebins -eq 1 ]
    then
    mv ${imroot}'-i-'${suffix}'-time0.mp' ${imroot}'-itime-'${suffix}'.mp'
    mv ${imroot}'-i-'${suffix}'-time0.bm' ${imroot}'-itime-'${suffix}'.bm'
    mv ${imroot}'-i-'${suffix}'-avg0.mp' ${imroot}'-iavg-'${suffix}'.mp'
    mv ${imroot}'-i-'${suffix}'-avg0.bm' ${imroot}'-iavg-'${suffix}'.bm'
else
    echo
    echo 'Sorry, I cannot parse that value of timebins!'
fi

# arithmetic on mp
maths exp='<'${imroot}'-itime-'${suffix}'.mp>-<'${imroot}'-iavg-'${suffix}'.mp>' out=${imroot}'-itime-'${suffix}'-sub.mp'

#echo
#echo '***Mean-subtracted image stats***'
#imstat in=${imroot}'-itime-'${suffix}'-sub.mp'

# clean map (lightly) and restore
clean map=${imroot}'-itime-'${suffix}'-sub.mp' beam=${imroot}'-itime-'${suffix}'.bm' out=${imroot}'-itime-'${suffix}'-sub.cl' niters=100 gain=0.02 region='relpixel,boxes(-'${cleansize}',-'${cleansize}','${cleansize}','${cleansize}')'
restor map=${imroot}'-itime-'${suffix}'-sub.mp' beam=${imroot}'-itime-'${suffix}'.bm' model=${imroot}'-itime-'${suffix}'-sub.cl' out=${imroot}'-itime-'${suffix}'-sub.rm'

echo
echo '***Restored image stats***'
imstat in=${imroot}'-itime-'${suffix}'-sub.rm'

imfit in=${imroot}'-itime-'${suffix}'-sub.rm' region='relpixel,boxes(-'${cleansize}',-'${cleansize}','${cleansize}','${cleansize}')' object=gaussian | grep Peak



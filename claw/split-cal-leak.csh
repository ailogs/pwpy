#!/usr/tcsh
#
# claw, 19jun09
# Script to calibrate ATA data with frequency dependent gains and leakages.
# Also outputs leakages for plotting by 'plotleak-realimag.py', in mmm code repository.
# Assumes the data is flagged.  Best to flag aggressively and remove any suspect antpols.

# User parameters
set src=c286  # source name, assuming 3c source
set freq=1480  # observing frequency
set point=qp6  # suffix for output file name.  originally used to differentiate pointing directions.
set visroot=hexc-3${src}-${point}-${freq} # file name
set chans=40  # channels per frequency chunk.  
#set flux=7.47 # flux of calibrator

# loop over frequency chunks
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32)

    # define first channel number of frequency chunk
    set startfreq = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=${visroot} out=${visroot}-${piece} line=ch,${chans},${startfreq} interval=0.001 options=nocal,nopass,nopol

    # these are a few obsolete steps
    #puthd in=${visroot}${piece}/evector value=1.570796
    #uvredo vis=${visroot}${piece} out=${visroot}${piece}.uvredo options=chi
    #rm -rf ${visroot}${piece};  mv ${visroot}${piece}.uvredo ${visroot}${piece}

    # now do cal steps.  mfcal for bandpass, gpcal for gains and leakages
    mfcal vis=${visroot}-${piece} refant=1 interval=5
    gpcal vis=${visroot}-${piece} refant=1 options=xyref interval=5 # options=xyref critical!  optionally may also use 'qusolve'
    gpcal vis=${visroot}-${piece} refant=1 options=xyref interval=5 # options=xyref critical!  optionally may also use 'qusolve' # do twice to get enough iters

    # now output the leakages for visualization later

    gpplt vis=${visroot}-${piece} options=polarization yaxis=amp log=3${src}-${point}-${freq}-leakamp${piece}.txt
    gpplt vis=${visroot}-${piece} options=polarization yaxis=phase log=3${src}-${point}-${freq}-leakphase${piece}.txt

    # rationalize leakage files for easy plotting by python script
    tail -n15 3${src}-${point}-${freq}-leakamp${piece}.txt > tmp
    cut -c1-28 tmp > tmp2
    cut -c29-56 tmp >> tmp2
    cut -c57- tmp >> tmp2
    mv tmp2 3${src}-${point}-${freq}-leakamp${piece}.txt
    rm -f tmp

    tail -n15 3${src}-${point}-${freq}-leakphase${piece}.txt > tmp
    cut -c1-28 tmp > tmp2
    cut -c29-56 tmp >> tmp2
    cut -c57- tmp >> tmp2
    mv tmp2 3${src}-${point}-${freq}-leakphase${piece}.txt
    rm -f tmp
end

#!/bin/bash

for mx in 4000 3500 3000 2800 2600 2500 2400 2200 2000 1800 1600 1400 1200 1000 900 800 700 600 500 400 360 320 300 280 240
do 
    for my in 60 70 80 90 100 125 150 190 250 300 350 400 450 500 600 700 800 900 1000 1100 1200 1300 1400 1600 1800 2000 2200 2400 2500 2600 2800
    do
        for tf in 0x0
        do
            echo "Running significance test for ${mx}-${my}"
            source scripts/unblinded_limits.sh -ws --sig "${mx}-${my}" --tf $tf
        done
    done
done

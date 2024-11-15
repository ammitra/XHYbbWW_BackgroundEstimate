#!/bin/bash

###########################################################################
# Script to run limits locally. The fits + limits are quick enough that 
# running them locally is not a major pain.
###########################################################################

for mx in 4000 3500 3000 2800 2600 2500 2400 2200 2000 1800 1600 1400 1200 1000 900 800 700 600 500 400 360 320 300 280 240
do 
    for my in 60 70 80 90 100 125 150 190 250 300 350 400 450 500 600 700 800 900 1000 1100 1200 1300 1400 1600 1800 2000 2200 2400 2500 2600 2800
    do
        for tf in 1x0 
        do
            if [ -f "${mx}-${my}_fits/NMSSM-XHY-${mx}-${my}-SR${tf}-VR${tf}_area/higgsCombine.AsymptoticLimits.mH125.42.root" ]; then 
                echo "Skipping $mx,$my - results already obtained"
            elif [ ! -d "${mx}-${my}_fits/" ]; then 
                echo "Skipping $mx,$my - no workspace exists"
            elif [ ! -f "${mx}-${my}_fits/base.root" ]; then 
                echo "Skipping $mx,$my - workspace exists but this mass point is missing samples."
            else 
                echo "------------------------------------------------------------------------"
                echo "${mx}-${my}"
                echo "------------------------------------------------------------------------"
                # Check if cards exist, make them if not
                if [ ! -f "${mx}-${my}_fits/NMSSM-XHY-${mx}-${my}-SR${tf}-VR${tf}_area/initialFitWorkspace.root" ]; then 
                    echo "Combine card for ${mx}-${my} does not exist, creating it first..."
                    ./scripts/run_blinded.sh --tf $tf --sig "${mx}-${my}" -w
                fi
                # Now check if the MultiDimFit snapshot exists. If not, make it first.
                if [ ! -f "${mx}-${my}_fits/NMSSM-XHY-${mx}-${my}-SR${tf}-VR${tf}_area/higgsCombineSnapshot.MultiDimFit.mH125.root" ]; then 
                    # Then run B-only MultiDimFit in VR, followed by AsymptoticLimits in SR
                    ./scripts/run_blinded.sh --sig "${mx}-${my}" --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin "-1" --rmax 2 --robustFit 0 -bl
                else
                    # Then run B-only MultiDimFit in VR, followed by AsymptoticLimits in SR
                    ./scripts/run_blinded.sh --sig "${mx}-${my}" --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin "-1" --rmax 2 --robustFit 0 -l
                fi
            fi 
        done
    done
done
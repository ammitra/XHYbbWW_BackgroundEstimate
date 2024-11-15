#!/bin/bash

sig=$1
SRtf=$2
VRtf=$3

mask_SR=""
mask_VR=""

cwd=$(pwd)

for region in SR_fail SR_pass VR_fail VR_pass;
do 
    for channel in LOW SIG HIGH
    do 
        for blind in false true;
        do
            if [[ $region == *"SR"* ]]; then 
                if [[ $blind == true ]]; then
                    mask_SR+="mask_${region}_${channel}=1,"
                else
                    mask_VR+="mask_${region}_${channel}=0,"
                fi;
            else
                if [[ $blind == true ]]; then 
                    mask_SR+="mask_${region}_${channel}=0,"
                else
                    mask_VR+="mask_${region}_${channel}=1,"
                fi;
            fi;
        done;
    done;
done; 

# remove trailing comma 
mask_SR=${mask_SR%,}
mask_VR=${mask_VR%,}

echo $mask_SR
echo $mask_VR

freeze_params_SR="var{Background_SR.*}"
freeze_params_VR="var{Background_VR.*}"

echo "cd ${sig}_fits/NMSSM-XHY-${sig}-SR${SRtf}-VR${VRtf}_area/"
cd "${sig}_fits/NMSSM-XHY-${sig}-SR${SRtf}-VR${VRtf}_area/"

if [ ! -f "higgsCombineSnapshot.MultiDimFit.mH125.root" ]; then 
    echo -e "\nERROR: higgsCombineSnapshot.MultiDimFit.mH125.root does not exist - run expected limits first."
fi

numtoys=500
seed=42

echo "GoF on data"
combine -M GoodnessOfFit -d higgsCombineSnapshot.MultiDimFit.mH125.root --algo saturated -m 120 \
--snapshotName MultiDimFit --bypassFrequentistFit \
--setParameters "${mask_SR},rgx{Background_SR_.*}=1,r=0"  \
--freezeParameters "r,${freeze_params_SR},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag" \
-n _gof_data -v 1 2>&1 | tee ./out_GoF_data.txt




echo "GoF on toys"
combine -M GoodnessOfFit -d higgsCombineSnapshot.MultiDimFit.mH125.root --algo saturated -m 120 \
--snapshotName MultiDimFit --bypassFrequentistFit \
--setParameters "${mask_SR},rgx{Background_SR_.*}=1,r=0"  \
--freezeParameters "r,${freeze_params_SR},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag" --saveToys \
-n _gof_toys -v 1 -s "$seed" -t "$numtoys" --toysFrequentist 2>&1 | tee ./out_GoF_toys.txt


cd $cwd

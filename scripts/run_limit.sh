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


echo "Blinded background-only fit (MC Blinded)"
combine -D data_obs -M MultiDimFit --saveWorkspace -m 125 -d initialFitWorkspace.root -v 2 \
--cminDefaultMinimizerStrategy 1 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000 \
--setParameters "${mask_SR},rgx{Background_SR_.*}=1,r=0"  \
--freezeParameters "r,${freeze_params_SR},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag" \
-n Snapshot 2>&1 | tee ./out_MultiDimFit.txt

seed=42

echo "Expected limits (MC Unblinded)"
combine -M AsymptoticLimits -m 125 -n "" -d higgsCombineSnapshot.MultiDimFit.mH125.root --snapshotName MultiDimFit -v 2 \
--saveWorkspace --saveToys --bypassFrequentistFit \
--setParameters "${mask_VR},rgx{Background_VR_.*}=1,r=0" \
--freezeParameters "${freeze_params_VR},var{.*_In},var{.*__norm},var{n_exp_.*}" -s "$seed" \
--floatParameters "${freeze_params_SR},r" --toysFrequentist --run blind 2>&1 | tee ./out_AsymptoticLimits.txt

cd $cwd

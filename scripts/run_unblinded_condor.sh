#!/bin/bash

######################################################
# Channel masking. We want to mask the VR.           #
######################################################
maskVR="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
setVR="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeVR="var{Background_VR.*},rgx{Background_VR.*}"
rmax=5
seed=123456
verbosity=2

# Run unblinded limits
echo "Unblinded Limits"
combine -M AsymptoticLimits -m 125 -n "" -d initialFitWorkspace.root -v $verbosity --rMax $rmax --saveWorkspace --saveToys -s $seed --toysFrequentist --setParameters "${maskVR},${setVR}" --freezeParameters "${freezeVR}"

ls -lh
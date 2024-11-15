#!/bin/bash

echo "background only fit of VR"

#combine -D data_obs -M MultiDimFit --saveWorkspace -m 125 -d WORKSPACE.root -v 9 \
#--cminDefaultMinimizerStrategy 1 --cminDefaultMinimizerTolerance 0.5  --X-rtd MINIMIZER_MaxCalls=400000 \
#--setParameters mask_SR_fail_HIGH=1,mask_SR_fail_LOW=1,mask_SR_fail_SIG=1,mask_SR_pass_HIGH=1,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_VR_fail_HIGH=0,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_pass_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,r=0,rgx{Background_SR_.*}=0 \
#--freezeParameters var{Background_SR.*} \
#-n Snapshot 2>&1 | tee MultiDimFit.txt

combine -M FitDiagnostics -m 125 -d WORKSPACE.root \
--setParameters mask_SR_fail_HIGH=1,mask_SR_fail_LOW=1,mask_SR_fail_SIG=1,mask_SR_pass_HIGH=1,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_VR_fail_HIGH=0,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_pass_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,rgx{Background_SR_.*}=0 \
--freezeParameters var{Background_SR.*} \
--cminDefaultMinimizerStrategy 1 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000 \
--rMin -1 --rMax 2 -v 2


vtol=0.3
stol=0.1
vtol2=2.0
stol2=0.5
regex="^(?!.*(_bin_|_par))"
python "$CMSSW_BASE"/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py fitDiagnosticsTest.root --abs -g nuisance_pulls.root --vtol=$vtol --stol=$stol --vtol2=$vtol2 --stol2=$stol2 --all --regex=$regex


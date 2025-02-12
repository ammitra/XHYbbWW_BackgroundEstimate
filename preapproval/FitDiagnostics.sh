#!/bin/bash

maskblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
maskunblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_SR_pass_HIGH=1,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_fail_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,mask_VR_pass_HIGH=0" # SR entirely masked off (except SR fail)
setparamsblinded="var{Background_SR_pass.*}=0,rgx{Background_SR_pass.*}=0"
setparamsunblinded="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeparamsblinded="var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
freezeparamsunblinded="var{Background_VR.*},rgx{Background_VR.*}"
unblindedparams="--freezeParameters ${freezeparamsunblinded},var{.*_In},var{.*__norm},var{n_exp_.*} --setParameters ${maskblindedargs},${setparamsunblinded}"

#echo "Making workspace"
#(set -x; text2workspace.py card.txt --channel-masks -o workspace.root) 2>&1 | tee outs/text2workspace.txt


echo "Fit Diagnostics (VR)"
mkdir -p outs
(set -x; combine -M FitDiagnostics -m 125 -d workspace.root \
--setParameters "${maskunblindedargs},${setparamsblinded}" \
--freezeParameters "${freezeparamsblinded}" --rMin -1 --rMax 2 \
--cminDefaultMinimizerStrategy 2 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000 \
-n Blinded --ignoreCovWarning -v 2) 2>&1 | tee outs/FitDiagnostics.txt

echo "Nuisance pulls (VR)"
vtol=0.3;stol=0.1;vtol2=2.0;stol2=0.5
regex='^(?!.*(_bin_|_par))'
python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py fitDiagnosticsBlinded.root --abs -g nuisance_pulls.root --vtol=${vtol} --stol=${stol} --vtol2=${vtol2} --stol2=${stol2} --all --regex="${regex}"
python nuisance_pulls.py


#echo "2D Fit Shapes"
#(set -x; PostFit2DShapesFromWorkspace --dataset "$dataset" -w ${wsm}.root --output FitShapes.root \
#-m 125 -f fitDiagnosticsBlinded.root:fit_b --postfit --print) 2>&1 | tee outs/FitShapes.txt


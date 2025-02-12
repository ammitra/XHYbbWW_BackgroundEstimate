#!/bin/bash

maskblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
maskunblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_SR_pass_HIGH=1,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_fail_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,mask_VR_pass_HIGH=0" # SR entirely masked off (except SR fail)
setparamsblinded="var{Background_SR_pass.*}=0,rgx{Background_SR_pass.*}=0"
setparamsunblinded="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeparamsblinded="var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
freezeparamsunblinded="var{Background_VR.*},rgx{Background_VR.*}"
unblindedparams="--freezeParameters ${freezeparamsunblinded},var{.*_In},var{.*__norm},var{n_exp_.*} --setParameters ${maskblindedargs},${setparamsunblinded}"

echo "dNLL scans (VR)"
mkdir -p outs
for p in Background_rpf_1x0_par0 Background_rpf_1x0_par1 CMS_bbWW_PNetHbb_mistag CMS_bbWW_PNetHbb_tag CMS_bbWW_PNetWqq_mistag CMS_bbWW_PNetWqq_tag CMS_l1_ecal_prefiring_2016 CMS_l1_ecal_prefiring_2017 CMS_pileup_2016 CMS_pileup_2017 CMS_pileup_2018 CMS_res_j_2016 CMS_res_j_2017 CMS_res_j_2018 CMS_res_jm_2016 CMS_res_jm_2017 CMS_res_jm_2018 CMS_scale_j_2016 CMS_scale_j_2017 CMS_scale_j_2018 CMS_scale_jm_2016 CMS_scale_jm_2017 CMS_scale_jm_2018 QCDscale_V QCDscale_ttbar lumi_13TeV_2016 lumi_13TeV_2017 lumi_13TeV_2018 lumi_correlated ps_fsr ps_isr; do
    if [[ $p == *"Background"* ]]; then 
        pMin=0.025;pMax=0.035
        yMax=2
    else
        pMin=-3;pMax=3
        yMax=8
    fi
    (set -x; combine -M MultiDimFit --algo grid -P $p workspace.root -n ".${p}" -m 120 --rMin -2 --rMax 2 --setParameterRanges $p=$pMin,$pMax --points 20 --floatOtherPOIs 1 --setParameters "${maskunblindedargs},${setparamsblinded}" --freezeParameters "${freezeparamsblinded}" --cminDefaultMinimizerStrategy 2 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000) 2>&1 | tee "outs/MultiDimFit_${p}.txt"    
    echo "Plotting dNLL for param $p"
    plot1DScan.py "higgsCombine.${p}.MultiDimFit.mH120.root" -o "dNLL_$p" --POI $p --y-max $yMax
done



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

seed=42

echo "Initial fit for impacts"
combineTool.py -M Impacts --snapshotName MultiDimFit -m 125 -n "impacts" \
-t -1 --bypassFrequentistFit --toysFrequentist --expectSignal 1 \
-d higgsCombineSnapshot.MultiDimFit.mH125.root --doInitialFit \
--setParameters "${mask_SR},rgx{Background_SR_.*}=1,r=0"  \
--freezeParameters "r,${freeze_params_SR},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag" \
# --setParameters "${mask_VR},rgx{Background_VR_.*}=1,r=0" \
# --freezeParameters "${freeze_params_SR},var{.*_In},var{.*__norm},var{n_exp_.*}" -s "$seed" \
# --floatParameters "${freeze_params_SR}" \
 --cminDefaultMinimizerStrategy=1 --cminDefaultMinimizerTolerance 0.1 \
 --X-rtd MINIMIZER_MaxCalls=400000 -v 2 2>&1 | tee ./out_Impacts_init.txt

params_to_scan="Background_rpf_1x0_par0,Background_rpf_1x0_par1,Background_SR_fail_LOW_bin_1-1,Background_SR_fail_LOW_bin_2-1,Background_SR_fail_LOW_bin_3-1,Background_SR_fail_LOW_bin_1-2,Background_SR_fail_LOW_bin_2-2,Background_SR_fail_LOW_bin_3-2,Background_SR_fail_LOW_bin_1-3,Background_SR_fail_LOW_bin_2-3,Background_SR_fail_LOW_bin_3-3,Background_SR_fail_LOW_bin_1-4,Background_SR_fail_LOW_bin_2-4,Background_SR_fail_LOW_bin_3-4,Background_SR_fail_LOW_bin_1-5,Background_SR_fail_LOW_bin_2-5,Background_SR_fail_LOW_bin_3-5,Background_SR_fail_LOW_bin_2-6,Background_SR_fail_LOW_bin_3-6,Background_SR_fail_SIG_bin_1-1,Background_SR_fail_SIG_bin_2-1,Background_SR_fail_SIG_bin_3-1,Background_SR_fail_SIG_bin_1-2,Background_SR_fail_SIG_bin_2-2,Background_SR_fail_SIG_bin_3-2,Background_SR_fail_SIG_bin_1-3,Background_SR_fail_SIG_bin_2-3,Background_SR_fail_SIG_bin_3-3,Background_SR_fail_SIG_bin_1-4,Background_SR_fail_SIG_bin_2-4,Background_SR_fail_SIG_bin_3-4,Background_SR_fail_SIG_bin_1-5,Background_SR_fail_SIG_bin_2-5,Background_SR_fail_SIG_bin_3-5,Background_SR_fail_SIG_bin_1-6,Background_SR_fail_SIG_bin_2-6,Background_SR_fail_SIG_bin_3-6,Background_SR_fail_SIG_bin_1-7,Background_SR_fail_SIG_bin_2-7,Background_SR_fail_SIG_bin_3-7,Background_SR_fail_SIG_bin_1-8,Background_SR_fail_SIG_bin_2-8,Background_SR_fail_SIG_bin_3-8,Background_SR_fail_SIG_bin_2-9,Background_SR_fail_SIG_bin_3-9,Background_SR_fail_HIGH_bin_1-1,Background_SR_fail_HIGH_bin_2-1,Background_SR_fail_HIGH_bin_3-1,Background_SR_fail_HIGH_bin_4-1,Background_SR_fail_HIGH_bin_1-2,Background_SR_fail_HIGH_bin_2-2,Background_SR_fail_HIGH_bin_3-2,Background_SR_fail_HIGH_bin_4-2,Background_SR_fail_HIGH_bin_1-3,Background_SR_fail_HIGH_bin_2-3,Background_SR_fail_HIGH_bin_3-3,Background_SR_fail_HIGH_bin_4-3,Background_SR_fail_HIGH_bin_1-4,Background_SR_fail_HIGH_bin_2-4,Background_SR_fail_HIGH_bin_3-4,Background_SR_fail_HIGH_bin_4-4,Background_SR_fail_HIGH_bin_1-5,Background_SR_fail_HIGH_bin_2-5,Background_SR_fail_HIGH_bin_3-5,Background_SR_fail_HIGH_bin_4-5,Background_SR_fail_HIGH_bin_1-6,Background_SR_fail_HIGH_bin_2-6,Background_SR_fail_HIGH_bin_3-6,Background_SR_fail_HIGH_bin_4-6,Background_SR_fail_HIGH_bin_1-7,Background_SR_fail_HIGH_bin_2-7,Background_SR_fail_HIGH_bin_3-7,Background_SR_fail_HIGH_bin_4-7,Background_SR_fail_HIGH_bin_1-8,Background_SR_fail_HIGH_bin_2-8,Background_SR_fail_HIGH_bin_3-8,Background_SR_fail_HIGH_bin_4-8,Background_SR_fail_HIGH_bin_1-9,Background_SR_fail_HIGH_bin_2-9,Background_SR_fail_HIGH_bin_3-9,Background_SR_fail_HIGH_bin_4-9,Background_SR_fail_HIGH_bin_2-10,Background_SR_fail_HIGH_bin_3-10,Background_SR_fail_HIGH_bin_4-10,Background_SR_fail_HIGH_bin_3-11,Background_SR_fail_HIGH_bin_4-11,CMS_bbWW_PNetHbb_mistag,CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_mistag,CMS_bbWW_PNetWqq_tag,CMS_bbww_TriggerWeight_2016,CMS_bbww_TriggerWeight_2017,CMS_bbww_TriggerWeight_2018,CMS_l1_ecal_prefiring_2016,CMS_l1_ecal_prefiring_2017,CMS_pileup_2016,CMS_pileup_2017,CMS_pileup_2018,CMS_res_j_2016,CMS_res_j_2017,CMS_res_j_2018,CMS_res_jm_2016,CMS_res_jm_2017,CMS_res_jm_2018,CMS_scale_j_2016,CMS_scale_j_2017,CMS_scale_j_2018,CMS_scale_jm_2016,CMS_scale_jm_2017,CMS_scale_jm_2018,QCDscale_V,QCDscale_ttbar,lumi_13TeV_2016,lumi_13TeV_2017,lumi_13TeV_2018,lumi_correlated,ps_fsr,ps_isr"

for p in Background_rpf_1x0_par0 Background_rpf_1x0_par1 Background_SR_fail_LOW_bin_1-1 Background_SR_fail_LOW_bin_2-1 Background_SR_fail_LOW_bin_3-1 Background_SR_fail_LOW_bin_1-2 Background_SR_fail_LOW_bin_2-2 Background_SR_fail_LOW_bin_3-2 Background_SR_fail_LOW_bin_1-3 Background_SR_fail_LOW_bin_2-3 Background_SR_fail_LOW_bin_3-3 Background_SR_fail_LOW_bin_1-4 Background_SR_fail_LOW_bin_2-4 Background_SR_fail_LOW_bin_3-4 Background_SR_fail_LOW_bin_1-5 Background_SR_fail_LOW_bin_2-5 Background_SR_fail_LOW_bin_3-5 Background_SR_fail_LOW_bin_2-6 Background_SR_fail_LOW_bin_3-6 Background_SR_fail_SIG_bin_1-1 Background_SR_fail_SIG_bin_2-1 Background_SR_fail_SIG_bin_3-1 Background_SR_fail_SIG_bin_1-2 Background_SR_fail_SIG_bin_2-2 Background_SR_fail_SIG_bin_3-2 Background_SR_fail_SIG_bin_1-3 Background_SR_fail_SIG_bin_2-3 Background_SR_fail_SIG_bin_3-3 Background_SR_fail_SIG_bin_1-4 Background_SR_fail_SIG_bin_2-4 Background_SR_fail_SIG_bin_3-4 Background_SR_fail_SIG_bin_1-5 Background_SR_fail_SIG_bin_2-5 Background_SR_fail_SIG_bin_3-5 Background_SR_fail_SIG_bin_1-6 Background_SR_fail_SIG_bin_2-6 Background_SR_fail_SIG_bin_3-6 Background_SR_fail_SIG_bin_1-7 Background_SR_fail_SIG_bin_2-7 Background_SR_fail_SIG_bin_3-7 Background_SR_fail_SIG_bin_1-8 Background_SR_fail_SIG_bin_2-8 Background_SR_fail_SIG_bin_3-8 Background_SR_fail_SIG_bin_2-9 Background_SR_fail_SIG_bin_3-9 Background_SR_fail_HIGH_bin_1-1 Background_SR_fail_HIGH_bin_2-1 Background_SR_fail_HIGH_bin_3-1 Background_SR_fail_HIGH_bin_4-1 Background_SR_fail_HIGH_bin_1-2 Background_SR_fail_HIGH_bin_2-2 Background_SR_fail_HIGH_bin_3-2 Background_SR_fail_HIGH_bin_4-2 Background_SR_fail_HIGH_bin_1-3 Background_SR_fail_HIGH_bin_2-3 Background_SR_fail_HIGH_bin_3-3 Background_SR_fail_HIGH_bin_4-3 Background_SR_fail_HIGH_bin_1-4 Background_SR_fail_HIGH_bin_2-4 Background_SR_fail_HIGH_bin_3-4 Background_SR_fail_HIGH_bin_4-4 Background_SR_fail_HIGH_bin_1-5 Background_SR_fail_HIGH_bin_2-5 Background_SR_fail_HIGH_bin_3-5 Background_SR_fail_HIGH_bin_4-5 Background_SR_fail_HIGH_bin_1-6 Background_SR_fail_HIGH_bin_2-6 Background_SR_fail_HIGH_bin_3-6 Background_SR_fail_HIGH_bin_4-6 Background_SR_fail_HIGH_bin_1-7 Background_SR_fail_HIGH_bin_2-7 Background_SR_fail_HIGH_bin_3-7 Background_SR_fail_HIGH_bin_4-7 Background_SR_fail_HIGH_bin_1-8 Background_SR_fail_HIGH_bin_2-8 Background_SR_fail_HIGH_bin_3-8 Background_SR_fail_HIGH_bin_4-8 Background_SR_fail_HIGH_bin_1-9 Background_SR_fail_HIGH_bin_2-9 Background_SR_fail_HIGH_bin_3-9 Background_SR_fail_HIGH_bin_4-9 Background_SR_fail_HIGH_bin_2-10 Background_SR_fail_HIGH_bin_3-10 Background_SR_fail_HIGH_bin_4-10 Background_SR_fail_HIGH_bin_3-11 Background_SR_fail_HIGH_bin_4-11 CMS_bbWW_PNetHbb_mistag CMS_bbWW_PNetHbb_tag CMS_bbWW_PNetWqq_mistag CMS_bbWW_PNetWqq_tag CMS_bbww_TriggerWeight_2016 CMS_bbww_TriggerWeight_2017 CMS_bbww_TriggerWeight_2018 CMS_l1_ecal_prefiring_2016 CMS_l1_ecal_prefiring_2017 CMS_pileup_2016 CMS_pileup_2017 CMS_pileup_2018 CMS_res_j_2016 CMS_res_j_2017 CMS_res_j_2018 CMS_res_jm_2016 CMS_res_jm_2017 CMS_res_jm_2018 CMS_scale_j_2016 CMS_scale_j_2017 CMS_scale_j_2018 CMS_scale_jm_2016 CMS_scale_jm_2017 CMS_scale_jm_2018 QCDscale_V QCDscale_ttbar lumi_13TeV_2016 lumi_13TeV_2017 lumi_13TeV_2018 lumi_correlated ps_fsr ps_isr
do 
    echo "Impact scan for parameter $p"
    # Impacts module cannot access parameters which were frozen in MultiDimFit, so running impacts
    # for each parameter directly using its internal command
    # (also need to do this for submitting to condor anywhere other than lxplus)
    combine -M MultiDimFit -n "_paramFit_impacts_$p" --algo impact --redefineSignalPOIs r -P "$p" \
    --floatOtherPOIs 1 --saveInactivePOI 1 --snapshotName MultiDimFit -d higgsCombineSnapshot.MultiDimFit.mH125.root \
    -t -1 --bypassFrequentistFit --toysFrequentist --expectSignal 1 --robustFit 1 \
    --freezeParameters "${freeze_params_VR},var{.*_In},var{.*__norm},var{n_exp_.*}" -s "$seed" \
    --floatParameters "${freeze_params_SR}" \
    --setParameterRanges r=-0.5,20 --cminDefaultMinimizerStrategy=1 --cminDefaultMinimizerTolerance 0.1 \
    --X-rtd MINIMIZER_MaxCalls=400000 -v 2 -m 125 | tee ./outImpacts_"$p".txt
done

echo "Collecting impacts"
combineTool.py -M Impacts --snapshotName MultiDimFit \
-m 125 -n "impacts" -d higgsCombineSnapshot.MultiDimFit.mH125.root \
--freezeParameters "${freeze_params_VR},var{.*_In},var{.*__norm},var{n_exp_.*}" -s "$seed" \
--floatParameters "${freeze_params_SR}" \
-t -1 --named "${params_to_scan}" \
--setParameterRanges r=-0.5,20 -v 1 -o impacts.json 2>&1 | tee ./out_Impacts_collect.txt

plotImpacts.py -i impacts.json -o impacts


cd $cwd

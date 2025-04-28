#!/bin/bash

maskVR="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
setVR="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeVR="var{Background_VR.*},rgx{Background_VR.*}"
floatParams='var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag'

wsm_snapshot='initialFitWorkspace'
strat=2
tol=10
verbosity=0
rmin=-20
rmax=20

ulimit -s unlimited


# combineTool.py -M Impacts --snapshotName initialFit -m 125 -n "impacts" --bypassFrequentistFit --toysFrequentist -d ${wsm_snapshot}.root --doInitialFit  --rMin $rmin --rMax $rmax --setParameters "${setVR},${freezeVR}" --cminDefaultMinimizerStrategy=$strat --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 -v $verbosity



# for p in Background_rpf_0x0_par0 CMS_bbWW_PNetHbb_mistag CMS_bbWW_PNetHbb_tag CMS_bbWW_PNetWqq_mistag CMS_bbWW_PNetWqq_tag CMS_l1_ecal_prefiring_2016 CMS_l1_ecal_prefiring_2017 CMS_pileup_2016 CMS_pileup_2017 CMS_pileup_2018 CMS_res_j_2016 CMS_res_j_2017 CMS_res_j_2018 CMS_res_jm_2016 CMS_res_jm_2017 CMS_res_jm_2018 CMS_scale_j_2016 CMS_scale_j_2017 CMS_scale_j_2018 CMS_scale_jm_2016 CMS_scale_jm_2017 CMS_scale_jm_2018 QCDscale_V QCDscale_ttbar lumi_13TeV_2016 lumi_13TeV_2017 lumi_13TeV_2018 lumi_correlated ps_fsr ps_isr;
# do
#     combine -M MultiDimFit -n "_paramFit_impacts_$p" -d ${wsm_snapshot}.root --algo impact --redefineSignalPOIs r -P "$p" --floatOtherPOIs 1 --saveInactivePOI 1 --snapshotName initialFit --bypassFrequentistFit --toysFrequentist --setParameters "${setVR},${maskVR}" --freezeParameters $freezeVR --floatParameters $floatParams --setParameterRanges r=-20,20 --cminDefaultMinimizerStrategy=$strat --robustHesse 1 --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 -v $verbosity -m 125
# done



named='Background_rpf_0x0_par0,CMS_bbWW_PNetHbb_mistag,CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_mistag,CMS_bbWW_PNetWqq_tag,CMS_l1_ecal_prefiring_2016,CMS_l1_ecal_prefiring_2017,CMS_pileup_2016,CMS_pileup_2017,CMS_pileup_2018,CMS_res_j_2016,CMS_res_j_2017,CMS_res_j_2018,CMS_res_jm_2016,CMS_res_jm_2017,CMS_res_jm_2018,CMS_scale_j_2016,CMS_scale_j_2017,CMS_scale_j_2018,CMS_scale_jm_2016,CMS_scale_jm_2017,CMS_scale_jm_2018,QCDscale_V,QCDscale_ttbar,lumi_13TeV_2016,lumi_13TeV_2017,lumi_13TeV_2018,lumi_correlated,ps_fsr,ps_isr'
combineTool.py -M Impacts --snapshotName initialFit -m 125 -n "impacts" -d ${wsm_snapshot}.root --floatParameters $floatParams --named $named --setParameterRanges r=-0.5,20 -v $verbosity -o impacts.json
plotImpacts.py -i impacts.json -o impacts


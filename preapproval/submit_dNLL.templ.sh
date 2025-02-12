#!/bin/bash

echo "Starting job on $$(date)" # Date/time of start of job
echo "Running on: $$(uname -a)" # Condor job is running on this node
echo "System software: $$(cat /etc/redhat-release)" # Operating System on that node

####################################################################################################
# Get my tarred CMSSW with combine already compiled
####################################################################################################

source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp -s root://cmseos.fnal.gov//store/user/ammitra/CMSSW_14_1_0_pre4_env.tgz .
export SCRAM_ARCH=el9_amd64_gcc12

echo "scramv1 project CMSSW CMSSW_14_1_0_pre4"
scramv1 project CMSSW CMSSW_14_1_0_pre4

echo "extracting tar"
tar -xf CMSSW_14_1_0_pre4_env.tgz
rm CMSSW_14_1_0_pre4_env.tgz
echo "CMSSW_14_1_0_pre4/src/"
cd CMSSW_14_1_0_pre4/src/
echo "pwd"
pwd
#echo "scramv1 b ProjectRename"
#scramv1 b ProjectRename # this handles linking the already compiled code - do NOT recompile
eval `scramv1 runtime -sh` # cmsenv is an alias not on the workers
echo $$CMSSW_BASE "is the CMSSW we have on the local worker node"
cd ../..

echo "ls -lh"

maskblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
maskunblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_SR_pass_HIGH=1,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_fail_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,mask_VR_pass_HIGH=0" # SR entirely masked off (except SR fail)
setparamsblinded="var{Background_SR_pass.*}=0,rgx{Background_SR_pass.*}=0"
setparamsunblinded="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeparamsblinded="var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
freezeparamsunblinded="var{Background_VR.*},rgx{Background_VR.*}"
unblindedparams="--freezeParameters ${freezeparamsunblinded},var{.*_In},var{.*__norm},var{n_exp_.*} --setParameters ${maskblindedargs},${setparamsunblinded}"


echo "dNLL scans (VR)"
set -x; combine -M MultiDimFit --algo grid -P $param workspace.root -n ".${param}" -m 120 --rMin -2 --rMax 2 --setParameterRanges $param=$pMin,$pMax --points 60 --floatOtherPOIs 1 --setParameters "${maskunblindedargs},${setparamsblinded}" --freezeParameters "${freezeparamsblinded}" --cminDefaultMinimizerStrategy 2 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000

echo "ls -lh"
ls -lh

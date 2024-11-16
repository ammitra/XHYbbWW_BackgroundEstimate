#!/bin/bash

# This script will do a FitDiagnostics routine on the Asimov SR and generate an output that 2DAlphabet can hopefully plot...
# This script should be run from the 2DAlphabet fit dir, e.g. $SIG_fits/NMSSM-XHY-$SIG-SR$TF-VR$TF_area/

# Do B-only, S+B fit of SR (asimov dataset) and create higgsCombineTest.FitDiagnostics.mH120.root
combine -M FitDiagnostics -d higgsCombineSnapshot.MultiDimFit.mH125.root --snapshotName MultiDimFit \
--setParameters mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1,rgx{Background_VR_.*}=1,r=1 \
--saveWorkspace --cminDefaultMinimizerStrategy 2 --rMin -1 --rMax 2 -v 2 --robustFit 0 --cminDefaultMinimizerTolerance 0.5 \
--freezeParameters var{Background_VR.*} --X-rtd MINIMIZER_MaxCalls=400000 \
--floatParameters var{Background_SR_fail.*},rgx{Background_SR_fail.*},var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag,r

workspace="higgsCombineTest.FitDiagnostics.mH120.root"
# Now make postfit shapes in a format that 2DAlphabet expects
for fit in b s
do 
    PostFit2DShapesFromWorkspace -w $workspace --output postfitshapes_"${fit}".root -f fitDiagnosticsTest.root:fit_"${fit}" --postfit --samples 100 --print
done 

# At this point you're done. To plot the SR (with SR_pass fully blinded), you need to edit 2DAlphabet/TwoDAlphabet/plot.py
# Under _make(self), you need to change the lines:
#
#                    full = stitch_hists_in_x(out2d_name, binning, [low,sig,high], blinded=blinding if process == 'data_obs' else [])
#                    full.SetMinimum(0)
#                    full.SetTitle('%s, %s, %s'%(proc_title,region,time))
#
# to:
#
#                    if (region == 'SR_pass') and (process == 'data_obs'):
#                        full = stitch_hists_in_x(out2d_name, binning, [low,sig,high], blinded=[0,1,2])
#                    else:
#                        full = stitch_hists_in_x(out2d_name, binning, [low,sig,high], blinded=[])
#                    full.SetMinimum(0)
#                    full.SetTitle('%s, %s, %s'%(proc_title,region,time))
#
# then immediately revert the changes when you're done.

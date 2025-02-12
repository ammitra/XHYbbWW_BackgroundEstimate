'''
Obtains the post-B-only-fit results from the VR fit and uses them as input to the dNLL scan as a function of `r` for the Asimov SR
'''
import ROOT
from TwoDAlphabet.helpers import execute_cmd

# Get the post-B-only-fit results
f = ROOT.TFile.Open('fitDiagnosticsBlinded.root')
fr = f.Get('fit_b')
pars = ROOT.RooArgList(fr.floatParsFinal())
par_vals = []
for i in range(pars.getSize()):
    par = pars[i]
    pname = par.GetName()
    if ('VR' in pname): continue
    postfitval = par.getValV()
    par_vals.append(f'{pname}={postfitval}')
# concatenate all of the postfit params
postfit_params=','.join(par_vals)

# Parameters for fit (mask+freeze VR params, set params to their VR postfit vals)
maskblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
setparamsunblinded="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeparamsunblinded="var{Background_VR.*},rgx{Background_VR.*}"

# fit options (no value set on signal expectation)
rMin=-1
rMax=1
combine_command = f'combine -M MultiDimFit --algo grid -P r workspace.root -n ".AsimovSR.r" -m 120 -t -1 --rMin {rMin} --rMax {rMax} --setParameterRanges r={rMin},{rMax} --points 100 --floatOtherPOIs 1 --setParameters {maskblindedargs},{setparamsunblinded},{postfit_params} --freezeParameters {freezeparamsunblinded} --cminDefaultMinimizerStrategy 2 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000'

execute_cmd(combine_command)

# Now use r=1 for the generated asimov toy
rMin=0
rMax=2
combine_command = f'combine -M MultiDimFit --algo grid -P r workspace.root -n ".AsimovSR.r1" -m 120 -t -1 --expectSignal=1 --rMin {rMin} --rMax {rMax} --setParameterRanges r={rMin},{rMax} --points 100 --floatOtherPOIs 1 --setParameters {maskblindedargs},{setparamsunblinded},{postfit_params} --freezeParameters {freezeparamsunblinded} --cminDefaultMinimizerStrategy 2 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000'

execute_cmd(combine_command)


ymax = 8
print('Plotting dNLL(r) for Asimov SR')
plot_command = f'plot1DScan.py "higgsCombine.AsimovSR.r.MultiDimFit.mH120.root" -o dNLL_AsimovSR_r --POI r --y-max {ymax}'
execute_cmd(plot_command)

# now plot for r=1
plot_command = f'plot1DScan.py "higgsCombine.AsimovSR.r1.MultiDimFit.mH120.root" -o dNLL_AsimovSR_r1 --POI r --y-max {ymax}'
execute_cmd(plot_command)

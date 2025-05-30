# Pre-approval homework

* Please share a slide showing the dNLL scans after the fit in the VR (and also for the SR once unblinded)
* Please share a slide showing the postfit nuisance parameter pulls after the fit to the VR data
* Please share a slide showing the prefit PU uncertainty template to better understand why it gets constrained strongly in the fit

All requested tests will be shown for the VR with an (1800,1200) GeV signal sample. 

## To run:

1. `./FitDiagnostics.sh` - runs FitDiagnostics and plots B-only and S+B nuisances in VR
2. `python submit_dNLL.py` - submits MultiDimFit jobs for all parameters, plots 1D scans of NLL as function of that parameter, and returns output products on condor.
    * can also be run locally via `./DeltaNLL.sh`, but not recommended b/c very slow

## dNLL scan as function of `r` in the Asimov SR

We want to show that dNLL as a function of `r` is healthy in the Asimov SR. To do this we will take the post-fit parameters from the b-only fit of the VR (contained in the `FitDiagnostics` output) and use them as input to the dNLL scan in the Asimov SR. 

To do this, run `python dNLL_r_AsimovSR.py`


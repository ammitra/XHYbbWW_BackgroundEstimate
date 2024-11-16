# XHYbbWW fitting 

This repository handles the fits and statistical tests for the $X \to H(b\bar{b})Y(WW\to 4q)$ analysis (semi-resolved $Y$). 

## Setting up the fit environment 

We use 2DAlphabet for the workspace and card creation, as well as post-fit plotting. To install it (on `el9` architecture, `cmslpc-el9.fnal.gov` only for the moment):

```bash
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v10.0.1
cd ../../
git clone --branch CMSWW_14_1_0_pre4 git@github.com:JHU-Tools/CombineHarvester.git
cd CombineHarvester/
cd ..
scramv1 b clean
scramv1 b -j 16
git clone --branch el9_matplotlib_plotting git@github.com:JHU-Tools/2DAlphabet.git
python3 -m virtualenv twoD-env
source twoD-env/bin/activate
cd 2DAlphabet/
python setup.py develop
```

## Statistical model 

The background estimate is performed using a statistical model comprising two-dimensional data and MC templates, with the dominant QCD background modeled using a data-driven estimate. The QCD in the Xbb-tag fail region is estimated by the difference between the data and the nominal (non-QCD) MC background there. The product of the QCD fail estimate and a transfer function formed by products of polynomials in $m_{X}$ and $m_{Y}$, whose parameter values are unconstrained in the likelihood, gives the QCD estimate in the Xbb-tag pass region. 

The Combine cards contain both SR and VR templates. The nuisance parameters for all processes are identical between the two regions except for the QCD fail/pass bins. The 2D templates are binned in $(m_{X},\, m_{Y})$, where the x-axis is split into `LOW/SIG/HIGH` mass bands for channel masking. This results in workspaces with 12 channel masks:

* `mask_SR_fail_LOW/SIG/HIGH` (3 masks)
* `mask_SR_pass_LOW/SIG/HIGH` (3 masks)
* `mask_VR_fail_LOW/SIG/HIGH` (3 masks)
* `mask_VR_pass_LOW/SIG/HIGH` (3 masks)

### Blinding via channel masks

The SR and VR are identically-defined except that the VR uses the Higgs mass sidebands ($75 \leq m_{H}^{reg} < 100$ or $150 < m_{H}^{reg} \leq 175$) and the SR uses the Higgs mass window ($100 \leq m_{H}^{reg} \leq 150$). We fit the VR independently to obtain the best-fit B-only parameter values (including that of the transfer function parameters) and then use those parameters to generate Asimov toys of the SR in which to obtain expected limits, impacts, and bias test results.

The general flow of the blinded fits is:

1. Make workspace 
2. Run B-only fit (via `MultiDimFit`) to obtain best-fit parameter values in the VR
3. Run expected limits in the SR (via `AsymptoticLimits`) using the best-fit B-only parameter values loaded from the `MultiDimFit` snapshot
4. Run `FitDiagnostics` to fit the VR again (for cross-check with `MultiDimFit` in step 1) and obtain postfit shapes for plotting and nuisance pulls
5. Run impacts for all parameters in SR with Asimov data 
6. Run bias tests with various injected signal strengths on the order of the expected limits 

The options to perform the various tests using the shell script are as follows:

wblsdgti
* `-w` : create workspace
* `-b` : B-only `MultiDimFit` of VR
* `-l` : `AsymptoticLimits` in Asimov SR, using postfit B-only param values
* `-s` : `Significance` test in Asimov SR
* `-d` : `FitDiagnosticsTest` in VR (B-only and S+B fits)
* `-g` : `GoodnessOfFit` test in data (VR)
* `-t` : `GoodnessOfFit` test in toys (VR)
* `-i` : `Impacts` initial fit 
   * `--impactsf [nuisance]` : `MultiDimFit` scan for a given nuisance parameter
   * `--impactsc`: collect all nuisance impacts, make impact plot 

Optional arguments, and values that give the most robust fits (in my experience):

* `--robustFit 0`
    * sometimes setting this to 1 helps the minimizer escape a local minimum
* `--rmin -1`
* `--rmax 2`
* `--tol 0.1` (default minimizer tolerance)
* `--strat 2` minimizer strategy 
    * Set the default minimizer strategy between 0 (speed), 1 (balance - default), 2 (robustness). The Minuit documentation for this is pretty sparse but in general, 0 means evaluate the function less often, while 2 will waste function calls to get precise answers. An important note is that the Hesse algorithm (for error and correlation estimation) will be run only if the strategy is 1 or 2.

## Step 1: Making workspaces 

2DAlphabet handles creating the workspaces, which requires a JSON configuration file and python script. 2DAlphabet will automatically produce all of the `RooFit` objects needed for the statistical model and store them in a `RooWorkSpace`. This procedure actually takes a really long time, so running them locally for a lot of signal mass points is somewhat time-prohibitive. **TODO: get 2DAlphabet to compile in a Condor node so that workspace creation can be run in parallel. I think it's just a pandas version issue...**

To create a workspace with the 2DAlphabet python script:
```
python VR.py --SRtf [tf] --VRtf [tf] -s [mx-my] -w "[mx-my]_" --make --makeCard
```
To create a workspace with the shell script (which just wraps the 2DAlphabet script):
```
./scripts/run_blinded.sh -w --tf [tf] --sig [mx-my]"
```

The `--make` flag handles creating the 2DAlphabet internal ledger and all of the `RooDataHist` and `RooParametricHist2D` objects for the workspace. This takes a long time because the fit model has 4 years (16APV, 16, 17, 18), five processes (ttbar, single top, W+jets, Z+jets, signal) and multiple shape nuisances for each process (each with an up/down variation). 

The `--makeCard` flag just creates the combined VR+SR card and `RooWorkspace` with channel masks. This is very quick, so if the 2DAlphabet workspace is already created, only pass this flag. 

## Step 2: Run B-only fit in VR

```
./scripts/run_blinded.sh --sig $sig --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin -1 --rmax 2 --robustFit 0 -b 
```

## Step 3: Run expected limits, Asimov SR 

Locally:
```
./scripts/run_blinded.sh --sig $sig --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin -1 --rmax 2 --robustFit 0 -l 
```

Condor:
```
python condor/submit_limits.py --sig 4000-2000 --tf 1x0 --seed 42 --tol 0.1 --strat 2
```
**NOTES:** 

* The condor submission script *only* needs the `card.txt` locally. You don't need to run `MultiDimFit` snapshot locally first
* The output from condor will be sent to the current working directory. Make sure to move it to the appropriate workspace automatically by using the script:
    * `python scripts/move_limits.py --tf $tf`
* After moving the condor outputs to their respective directories, run
    * `python scripts/2Dlims.py`


## Step 4: Run `FitDiagnostics` in VR

```
./scripts/run_blinded.sh --sig $sig --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin -1 --rmax 2 --robustFit 0 -d 
```

## Step 5: Run impacts, Asimov SR 

First run `Impacts` on its own:
```
./scripts/run_blinded.sh --sig $sig --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin -1 --rmax 2 --robustFit 0 -i
```

Then run `MultiDimFit` scans for all parameters.
```
params=`python scripts/get_parameters_for_impacts.py`   # get all parameters for eval (skipping QCD bins)
for p in $params; do ./scripts/run_blinded.sh --sig $sig --tf $tf --tol 0.1 --strat 2 --verbosity 2 --impactsf $p; done 
```

Then collect all parameter impacts:
```
./scripts/run_blinded.sh --sig $sig --tf $tf --verbosity 2 --tol 0.1 --strat 2 --rmin -1 --rmax 2 --robustFit 0 --impactsc 1
```

## Step 6: Run bias tests, Asimov SR 

First run expected limits to get an idea for how much signal to inject. Then run the limits using condor.

To run 500 toys (50 jobs, 10 toys/job), run:
```
python condor/submit_bias.py --sig $sig --tf $tf --toys-per-job 10 --num-jobs 50 --bias $bias
```

The condor submission script for bias tests requires that the `MultiDimFit` snapshot exists locally. The reason is that we want to verify that the fit worked well and the best-fit B-only parameters make sense before submitting the condor jobs, rather than doing workspace creation + B-only fit in the condor node. 

The option arguments `--seed`, `--strat`, `--tol`, `--rmin`, `--rmax` can be passed to the python script as well, but they already default to the optimal values. 

The outputs will be sent to the current working directory, so make sure to `mv` them to the proper workspace after they've finished. 

After moving the output, plot the bias test results using 
```
python scripts/plot_bias.py --tf $tf --sig $sig --bias $bias
```


## Extra scripts 

Located in the `scripts/` directory:

* `get_lumi_unc.py`: obtain the luminosity uncertainties for use in the 2DAlphabet JSON
* `get_parameters_for_impacts.py`: prints all of the named nuisance parameters except for QCD bins for use in the impacts script. 
* `make_cards.sh`: calls the `VR.py` 2DAlphabet script to create the workspace and combined cards for all signals. Running this will take literally forever but it's the only way until I sort out 2DAlphabet compilation in condor nodes
* `make_systematic_plots.py`: uses 2DAlphabet to produce plots of all processes subject to their systematic uncertainties. Just specify a workspace directory. Requires that the workspace exists
* `plot_gof.py`: plots the goodness of fit results from the VR
* `compare_nuisances.py`: compares the nuisance parameters b/w the `FitDiagnosticsTest` and `MultiDimFit` results to ensure compatibility with one another. 
* `find_missing_signals.py`: loops over all possible mass points and checks (for kinematically-allowed mass points) whether all templates are available. If the mass point is missing some centrally-produced files, it outputs the signal name and missing years to a JSON file. Otherwise, if there are not the expected number of template files due to some mistake in selection, it saves them to a text file for later checks. 
* `run_limits.sh`: loops over all signal mass points and creates the combined card + `RooWorkspace` (if they do not exist), runs B-only `MultiDimFit` (if snapshot does not already exist), then `AsymptoticLimits` locally. **Warning:** this will take a while to run locally. You should use the condor submission explained above.
* `make_RooWorkspace.sh`: runs locally, generates the cards + `RooWorkspace` for all signal mass points. 
# Unblinding 

We follow the [incremental unblinding procedure](https://twiki.cern.ch/twiki/bin/viewauth/CMS/B2G#Analysis_Reviews_and_Pre_approva) outlined by the B2G PAG.

This directory will act as the workspace for the incremental unblinding of a single signal mass point, arbitrarily chosen as $(m_X,\, m_Y) = (1800,1200)$ GeV. 

1. F-Test on the full SR distribution to determine the best TF parameterization. 
2. Unblinded GoF 
3. Impacts on the full SR distributions 
   * First with the signal strength blinded 
   * Then with the signal strength revealed
4. Unblinded signal region distributions (with pre-fit+post-fit background only) 
5. Derive observed limits (and post-fit expected limits) and signal strength/significance for the largest deviation (excess/deficit) observed 

## 1) F-tests

First run the FitDiagnostics for the mass point with different transfer functions:

```
python B2G_unblinding/unblind.py --makeCard --fit --tf [tf]
```

Generally the most stable options are: `--robustFit --strat 0` with a low `--rMax` (usually less than 5). 

Then you can run the F-tests with 

```
python B2G_unblinding/unblind.py --poly1 [tf1] --poly2 [tf2] --FTest --tf foobar
```

where `--poly1` represents the lower-order polynomial (subset of `--poly2`), and `--tf` is just a dummy argument. 

## 2) GoF 

After determining best TF parameterization by F-test, run GoF:

```
python B2G_unblinding/unblind.py --tf [tf] --gof <args>
```

## 3) Impacts 

```
python B2G_unblinding/unblind.py --tf [tf] --impacts
```

## 4) Postfit distributions

If you want the 2DAlphabet plots:
```
python B2G_unblinding/unblind.py --tf [tf] --plot
```

If you want the 1D projections for the paper:
```
python B2G_unblinding/paper_plots.py [--prefit]
```

where `--prefit` will plot the prefit distributions instead of postfit (the default). Note that prefit distributions will be weird due to how 2DAlphabet initializes the QCD and TF values.


import os, glob
import numpy as np
from scipy import interpolate
import matplotlib
import matplotlib.pyplot as plt
import mplhep as hep
import matplotlib.ticker as mticker
import ROOT
import subprocess
import pandas as pd

plt.style.use(hep.style.CMS)
hep.style.use("CMS")
formatter = mticker.ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 3))
plt.rcParams.update({"font.size": 20})

def mxmy(sample):
    mX = float(sample.split('/')[0].split('_')[0].split('-')[0])
    mY = float(sample.split('/')[0].split('_')[0].split('-')[1])
    return (mX, mY)

# Grab significance files
files = glob.glob('*_fits/Unblinded_0x0/higgsCombine.Significance.mH125.123456.root')

sig_pval = {'significance': [], 'pvalue': []}

for sample in files:
    mx, my = mxmy(sample)
    if (mx < 800):
        continue
    if (my < 300):
        continue
    print(f'Processing sample ({mx},{my})')
    # Get the significance for this mass point 
    f = ROOT.TFile.Open(sample,'READ')
    limTree = f.Get('limit')
    if not limTree:
        print(f'WARNING: Skipping ({mx},{my}) since limit tree does not exist')
        continue
    limTree.GetEntry(0)
    significance = limTree.limit 
    pvalue = ROOT.RooStats.SignificanceToPValue(significance)
    # Store the values 
    sig_pval['significance'].append([mx,my,significance])
    sig_pval['pvalue'].append([mx,my,pvalue])

# Convert to np arrays
for key in sig_pval:
    sig_pval[key] = np.array(sig_pval[key])

# Store the significance and p-values as CSV files and plot
for key, val in sig_pval.items():
    # CSV generation
    col_name = 'Significance (sigma)' if key == 'significance' else 'p-value'
    df = pd.DataFrame(val, columns=['MX','MY',col_name])
    df.to_csv(f'limits/{key}.csv')

    print(df.sort_values(by='Significance (sigma)'))
    '''
    # Plot 
    xbins = np.arange(800,4600,100)
    ybins = np.arange(800,4600,100)
    xs = list(dict.fromkeys(df.sort_values(by='MX')['MX']))
    ys = list(dict.fromkeys(df.sort_values(by='MY')['MY']))


    
    xy  = val[:, :2]
    obs = val[:, 2]
    print(obs)
    exit()
    print('-----------------------------------------------------')
    print(key)
    print(xy)
    '''

def hist2d(arr, title, name):
    fig, ax = plt.subplots(figsize=(14,12))
    hep.hist2dplot(arr,flow=None)
    ax.set_xlabel(r'$m_{X}$ [GeV]')
    ax.set_ylabel(r'$m_{Y}$ [GeV]')
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)
    plt.savefig(name, bbox_inches="tight")


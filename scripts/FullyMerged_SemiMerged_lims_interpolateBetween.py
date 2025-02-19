'''
script to plot limits from both the semi-resolved and fully-merged analysis

IMPORTANT:

We will interpolate between Raghav's 250 GeV and my ~350 GeV limits to eliminate 
the region between the two analyses where we are both not sensitive. 
'''

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

# 0-4 are m2,m1,exp,p1,p2 sigma limits, 5 is observed
limits = {0: [], 1: [], 2: [], 3: [], 4: []}

# First do all of my files 
files = glob.glob('*_fits/NMSSM*/higgsCombine.AsymptoticLimits.*')
for sample in files:
    mx, my = mxmy(sample)
    if (mx < 800): continue # skip Raghav's mass points
    if (my < 300): continue # skip Raghav's mass points
    if (mx >= 1300) and ((my >= 300) and (my <= 400)): continue # skip the signals i'm not sensitive to
    print('Processing sample ({},{})'.format(mx,my))
    # loop over m2 to p2 sigma 
    f = ROOT.TFile.Open(sample,'READ')
    limTree = f.Get('limit')
    if not limTree.GetEntry(2): continue # skip if no med exp limit 
    for i in range(5): # skip observed for now
        # The input normalization is all in picobarns (1pb = 1000fb)
        # So we multiply all limits by the input cross section in fb
        limTree.GetEntry(i)
        if mx < 1000: 
            signalNorm = 0.1 * (1000.)
        elif (mx >= 1000) and (mx < 2000): 
            signalNorm = 0.01 * (1000.)
        elif (mx >= 2000): 
            signalNorm = 0.001 * (1000.)
        limit = limTree.limit * signalNorm
        limits[i].append([mx, my, limit])


# Now get Raghav's limits
redir = 'root://cmseos.fnal.gov'
limdir = '/store/user/rkansal/bbVV/cards/Apr11'
raghav_lims = subprocess.check_output(f'eos {redir} ls {limdir}',shell=True,text=True)
raghav_lims = raghav_lims.split()
for ld in raghav_lims:
    if (my > 250): continue
    mx = float(ld.split('_')[2].split('-')[-1])
    my = float(ld.split('_')[3].split('-')[-1])
    f = ROOT.TFile.Open(f'{redir}/{limdir}/{ld}/higgsCombinepass.AsymptoticLimits.mH125.123456.root','READ')
    limTree = f.Get('limit')
    if not limTree.GetEntry(2): continue # skip if no med exp limit 
    for i in range(5): 
        limTree.GetEntry(i)
        limit = limTree.limit
        limits[i].append([mx, my, limit])



for key in limits:
    limits[key] = np.array(limits[key])

for key, limit in limits.items():
    df = pd.DataFrame(limit, columns=["MX", "MY", "Limit (fb)"])
    labels = {
        0: 'Minus2',
        1: 'Minus1',
        2: 'Expected',
        3: 'Plus1',
        4: 'Plus2',
        5: 'OBSERVED'
    }
    df.to_csv(f"limits/limits_{labels[key]}_COMBINED-ANALYSES-INTERP-BETWEEN.csv")

def scatter2d(arr, title, name):
    fig, ax = plt.subplots(figsize=(14, 12))
    mappable = plt.scatter(
        arr[:, 0],
        arr[:, 1],
        s=150,
        c=arr[:, 2],
        cmap="turbo",
        norm=matplotlib.colors.LogNorm(vmin=0.01, vmax=100),
    )
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(mappable,label=title)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)

    # separate the two analysis
    ax.hlines(y=300.0, xmin=800.0, xmax=4010.0, color='black', linestyle='dashed')
    ax.vlines(x=800.0, ymin=300.0, ymax=2810.0, color='black', linestyle='dashed')
    ax.text(0.3, 0.95, 'Semi-resolved Y', ha='center', va='top', fontsize='small', transform=ax.transAxes)

    plt.savefig(name, bbox_inches="tight")

def colormesh(xx, yy, lims, label, name):
    fig, ax = plt.subplots(figsize=(12, 8))
    _ = plt.pcolormesh(
        xx, yy, lims, norm=matplotlib.colors.LogNorm(vmin=0.05, vmax=1e4), cmap="turbo"
    )
    # plt.title(title)
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(label=label)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)

    # separate the two analysis
    ax.hlines(y=300.0, xmin=800.0, xmax=4010.0, color='black', linestyle='dashed')
    ax.vlines(x=800.0, ymin=300.0, ymax=2810.0, color='black', linestyle='dashed')
    ax.text(0.3, 0.95, 'Semi-resolved Y', ha='center', va='top', fontsize='small', transform=ax.transAxes)

    plt.savefig(name, bbox_inches="tight")

# mx masses
mxs = np.logspace(np.log10(100), np.log10(3999), 100, base=10)
mys = np.logspace(np.log10(10), np.log10(2799), 100, base=10)

xx, yy = np.meshgrid(mxs, mys)

interpolated = {}
grids = {}

for key, val in limits.items():
    interpolated[key] = interpolate.LinearNDInterpolator(val[:, :2], np.log(val[:, 2]))
    grids[key] = np.exp(interpolated[key](xx, yy))


for key, grid in grids.items():
    if key == 0: label = '2.5'
    elif key == 1: label = '16.0'
    elif key == 2: label = '50.0'
    elif key == 3: label = '84.0'
    elif key == 4: label = '97.5'
    t = '%s expected exclusion limits (fb)'%('Median' if label=='50.0' else label+'%')
    colormesh(xx, yy, grid, t, "plots/limit2D_interp_{}_COMBINED-ANALYSES-INTERP-BETWEEN.pdf".format(label))

for key in range(5):
    if key == 0: label = '2.5'
    elif key == 1: label = '16.0'
    elif key == 2: label = '50.0'
    elif key == 3: label = '84.0'
    elif key == 4: label = '97.5'
    val = limits[key]
    t = '%s expected exclusion limits (fb)'%('Median' if label=='50.0' else label+'%')
    scatter2d(val, t, "plots/limit2D_scatter_{}_COMBINED-ANALYSES-INTERP-BETWEEN.pdf".format(label))

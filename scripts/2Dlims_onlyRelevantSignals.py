'''
Since the fits are only binned from [800, 4500] in mX and [300, 4500] in mY, limits for all signals outside of this region are pretty much meaningless. So, this script plots the limits only for the signals in this window. 
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

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('--unblinded', dest='unblinded', action='store_true')

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

if args.unblinded:
    files = glob.glob('*_fits/Unblinded_0x0/higgsCombine.AsymptoticLimits.*')
    limits[5] = []
else:
    files = glob.glob('*_fits/NMSSM*/higgsCombine.AsymptoticLimits.*')

for sample in files:
    mx, my = mxmy(sample)
    if (mx < 800) or (my < 300):
        continue 
    print('Processing sample ({},{})'.format(mx,my))
    # loop over m2 to p2 sigma 
    f = ROOT.TFile.Open(sample,'READ')
    limTree = f.Get('limit')
    if not limTree.GetEntry(2): continue # skip if no med exp limit 
    r = 6 if args.unblinded else 5
    for i in range(r): # skip observed for now
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

for key in limits:
    limits[key] = np.array(limits[key])

def scatter2d(arr, title, name):
    fig, ax = plt.subplots(figsize=(14, 12))
    mappable = plt.scatter(
        arr[:, 0],
        arr[:, 1],
        s=150,
        c=arr[:, 2],
        cmap="viridis",
        norm=matplotlib.colors.LogNorm(vmin=0.01, vmax=100),
    )
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(mappable,label=title)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)
    plt.savefig(name, bbox_inches="tight")

def colormesh(xx, yy, lims, label, name):
    fig, ax = plt.subplots(figsize=(12, 8))
    _ = plt.pcolormesh(
        xx, yy, lims, norm=matplotlib.colors.LogNorm(vmin=0.05, vmax=1e4), cmap="viridis"
    )
    # plt.title(title)
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(label=label)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)
    plt.savefig(name, bbox_inches="tight")

# mx masses
mxs = np.logspace(np.log10(799), np.log10(3999), 100, base=10)
mys = np.logspace(np.log10(299), np.log10(2799), 100, base=10)

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
    elif key == 5: label = 'Observed'
    t = '95% CL %s expected upper limits (fb)'%('Median' if label=='50.0' else label+'%')
    colormesh(xx, yy, grid, t, "plots/limit2D_interp_{}_zoomed.pdf".format(label))

for key in range(5):
    if key == 0: label = '2.5'
    elif key == 1: label = '16.0'
    elif key == 2: label = '50.0'
    elif key == 3: label = '84.0'
    elif key == 4: label = '97.5'
    elif key == 5: label = 'Observed'
    val = limits[key]
    t = '95% CL %s expected upper limits (fb)'%('Median' if label=='50.0' else label+'%')
    scatter2d(val, t, "plots/limit2D_scatter_{}_zoomed.pdf".format(label))

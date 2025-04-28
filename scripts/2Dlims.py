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
args = parser.parse_args()

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
    df.to_csv(f"limits/limits_{labels[key]}.csv")

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
    pcol = plt.pcolormesh(xx, yy, lims, norm=matplotlib.colors.LogNorm(vmin=0.05, vmax=1e4), cmap="viridis",linewidth=0, rasterized=True)
    pcol.set_edgecolor('face')
    # plt.title(title)
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(label=label)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)
    plt.savefig(name, bbox_inches="tight")

# mx masses
mxs = np.logspace(np.log10(400), np.log10(3999), 100, base=10)
mys = np.logspace(np.log10(50), np.log10(2799), 100, base=10)

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

    if key < 5:
        t = f'95% CL {label}% expected upper limits (fb)'
    else:
        t = 'Observed upper limit (fb)'
    colormesh(xx, yy, grid, t, "plots/limit2D_interp_{}.pdf".format(label.replace('.','p')))

for key in range(6):
    if key == 0: label = '2.5'
    elif key == 1: label = '16.0'
    elif key == 2: label = '50.0'
    elif key == 3: label = '84.0'
    elif key == 4: label = '97.5'
    elif key == 5: label = 'Observed'
    val = limits[key]

    if key < 5:
        t = f'95% CL {label}% expected upper limits (fb)'
    else:
        t = 'Observed upper limit (fb)'
    scatter2d(val, t, "plots/limit2D_scatter_{}.pdf".format(label.replace('.','p')))

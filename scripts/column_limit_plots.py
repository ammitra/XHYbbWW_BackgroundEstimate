'''
Script to generate a 4x4 grid of plots for 1D limits as a function of mY for different mX values.
Similar to those made by Xanda:
    - https://www.dropbox.com/scl/fi/t1h7qcb5e1hby75ixeme6/HY_bbWW4q_examples.pdf?rlkey=mp6b5qv7w64ajweqkthwimhaw&e=1&dl=0
    - https://gitlab.cern.ch/acarvalh/generalsummary/-/blob/B2G-23-002/specific_interpretations/HYPlot/DrawHYPlot.py?ref_type=heads
    - https://indico.cern.ch/event/1337889/contributions/5694589/attachments/2770171/4826694/PhysicsDays_HY_progress_Dec2023.pdf

Fits for semi-resolved Y analysis start at 800 in mX and 300 in mY.
'''
import os, glob
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import mplhep as hep
import matplotlib.ticker as mticker
import ROOT
import subprocess
import pandas as pd
from collections import OrderedDict

# Main plotting routine for each axes
def plot_limit_1D(ax, x_axis_vals, xMass, m2, m1, med, p1, p2):
    '''
    pass numpy arrays for the +/-1, +/-2, and median expected limits and the axes on which to draw.
    '''
    green = '#607641' 
    yellow = '#F5BB54'

    ax.grid(True, axis='y', linestyle='dashed')

    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlim([200, 3500])    # the x-axis is plotting mY 
    ax.set_ylim([1e-2, 1e6])    # the y-axis is plotting xsec * BR limit 

    locmin = mticker.LogLocator(base=10.0,subs=(0.2,0.4,0.6,0.8),numticks=12)
    ax.xaxis.set_minor_locator(locmin)
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_minor_locator(locmin)
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

    ax.fill_between(x_axis_vals, m2, p2, color=yellow, label=r'$\pm 2\sigma$')
    ax.fill_between(x_axis_vals, m1, p1, color=green, label=r'$\pm 1\sigma$')
    ax.plot(x_axis_vals, med, color='black', linestyle='--', label='Expected 95% CL limit')

    ax.text(0.3, 0.95, r'$m_{X} = %s$ GeV'%(xMass), ha='center', va='top', fontsize='small', transform=ax.transAxes)


# X and Y masses for consideration
xs = ['800', '900', '1000', '1200', '1400', '1600', '1800', '2000', '2200', '2400', '2500', '2600', '2800', '3000', '3500', '4000']
ys = ['300', '350', '400', '450', '500', '600', '700', '800', '900', '1000', '1100', '1200', '1300', '1400', '1600', '1800', '2000', '2200', '2400', '2500', '2600', '2800']

# 0: minus2, 1: minus2, 2: median, 3: plus1, 4: plus2, 5: observed
dfs  = {0:None, 1:None, 2:None, 3:None, 4:None}
sigs = OrderedDict([(mx,dfs.copy()) for mx in xs])

# Now populate the dfs dict with the full dataframes of all the limits 
for i in range(len(dfs)):
    if i == 0:
        fname = 'limits/limits_Minus2.csv'
    elif i == 1:
        fname = 'limits/limits_Minus1.csv'
    elif i == 2:
        fname = 'limits/limits_Expected.csv'
    elif i == 3:
        fname = 'limits/limits_Plus1.csv'
    elif i == 4:
        fname = 'limits/limits_Plus2.csv'
    else:
        raise ValueError(f'Have not yet run observed limits (i=={i})')
    lim = pd.read_csv(fname)
    dfs[i] = lim

# Store the dataframes for the median, +/-1 sigma, +/-2 sigma, and observed limits.
for mx in xs:
    for lim in range(len(dfs)):
        df = dfs[lim]
        df = df[df['MX'] == float(mx)]
        sigs[mx][lim] = df.sort_values(by='MY')

# At this point, all 16 mX values have their 4 limits stored in pandas dfs as a function of mY.
hep.cms.text("WiP",loc=0)
lumiText = "138 $fb^{-1} (13 TeV)$"    
hep.cms.lumitext(lumiText)
fig, axes = plt.subplots(4, 4, figsize=(10,10), dpi=150, sharex=True, sharey=True)
axes = axes.flatten()
for i, mX in enumerate(xs):
    ax = axes[i]
    lims = sigs[mX]
    y_vals = lims[0]['MY'].values # just grab the minus2 key as a dummy key to get they Y-vals. All keys should give the same
    m2  = lims[0]['Limit (fb)'].values
    m1  = lims[1]['Limit (fb)'].values
    med = lims[2]['Limit (fb)'].values
    p1  = lims[3]['Limit (fb)'].values
    p2  = lims[4]['Limit (fb)'].values
    plot_limit_1D(
        ax = ax, 
        x_axis_vals = y_vals, 
        xMass = mX, 
        m2 = m2, 
        m1 = m1, 
        med = med,
        p1 = p1, 
        p2 = p2
    )
    # until I figure out a better way to apply a common x/y-axis label to subplots...
    if i == 0:
        ax.set_ylabel(r"$\sigma$(pp $\to$ X $\to$ HY) $\times$ B(bb WW) (fb)")
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='lower right', fontsize=8, frameon=True) # Draw legend with box so it doesn't get obscured by gridlines
        lumiText = "138 $fb^{-1}$ (13 TeV)" 
        hep.cms.text("WiP",loc=0,ax=ax)
        hep.cms.lumitext(lumiText,ax=ax)

    if i == len(xs)-1:
        ax.set_xlabel(r"$m_{Y}$ (GeV)",loc='right')


fig.tight_layout()
plt.savefig('plots/column_limits_1D.pdf')
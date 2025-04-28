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

df = pd.read_csv('limits/significance.csv')
df = df.sort_values(['Significance (sigma)'], ascending=[True])

vals = []

for i in range(len(df)):
    vals.append(df.iloc[i].to_numpy()[1:]) # start from index 1 to get rid of the DF row number


def scatter2d(arr, title, name):
    fig, ax = plt.subplots(figsize=(14, 12))
    mappable = plt.scatter(
        arr[:, 0],
        arr[:, 1],
        s=150,
        c=arr[:, 2],
        cmap="viridis",
        #norm=matplotlib.colors.LogNorm(vmin=0.01, vmax=100),
    )
    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$m_{Y}$ (GeV)")
    plt.colorbar(mappable,label=title)
    hep.cms.label("Work in Progress", data=True, lumi="138", ax=ax)
    plt.savefig(name, bbox_inches="tight")

t = 'Observed local significance (sigma)'
scatter2d(np.array(vals), t, "plots/significance_2D_scatter.pdf")

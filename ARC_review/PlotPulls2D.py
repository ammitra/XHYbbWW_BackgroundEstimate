'''
Script to answer the following ARC question:
"Can you provide the pulls for the bins used in the analysis in a 2D plot?"
'''
import ROOT, uproot 
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
from helpers import *
import os
import scipy

def add_cms_label(ax, year, data=True, label="Preliminary", loc=2, lumi=True):
    if year == "all":
        hep.cms.label(
            label,
            data=data,
            lumi='138',
            year=None,
            ax=ax,
            loc=loc,
        )
    else:
        hep.cms.label(
            label,
            data=data,
            #lumi=f"{LUMI[year] / 1e3:.0f}" if lumi else None,
            year=year,
            ax=ax,
            loc=loc,
        )


# Create TH2s and save to root file for uproot
input_file = '../B2G_unblinding/largest_significance_1200-900_postfit/Unblinded_0x0/postfitshapes_b.root'

procs = ['TotalBkg','data_obs']
for y in ['16','16APV','17','18']:
    procs.append(f'NMSSM-XHY-1200-900_{y}')
histos_TH2 = {}
histos_TH2['SR_pass'] = get_hists(input_file,'SR_pass',procs,prefit=False)



out = ROOT.TFile.Open('PostfitDistributions_SR_pass.root','RECREATE')
out.cd()

for k,v in histos_TH2['SR_pass'].items():
    v.SetName(k)
    v.SetTitle(k)
    v.Write()

# Make a histogram of bkg uncertainty
bkg = histos_TH2['SR_pass']['TotalBkg']
unc = bkg.Clone('BkgUnc')
unc.Reset()
for i in range(1,bkg.GetNbinsX()+1):
    for j in range(1,bkg.GetNbinsY()+1):
        err = bkg.GetBinError(i,j)
        unc.SetBinContent(i,j,err)
unc.Write()
# Make a histogram of data uncert
data = histos_TH2['SR_pass']['data_obs']
unc = data.Clone('DataUnc')
unc.Reset()
for i in range(1,data.GetNbinsX()+1):
    for j in range(1,data.GetNbinsY()+1):
        err = data.GetBinError(i,j)
        unc.SetBinContent(i,j,err)
unc.Write()

# Make a histogram of the signals 
# for y in ['16','16APV','17','18']:
#     dummy = histos_TH2['SR_pass'][f'NMSSM-XHY-1200-900_{y}']
#     sig = dummy.Clone(f'NMSSM-XHY-1200-900_{y}')
#     sig.Reset()
#     for i in range(1,dummy.GetNbinsX()+1):
#         for j in range(1,dummy.GetNbinsY()+1):
#             val = dummy.GetBinError(i,j)
#             sig.SetBinContent(i,j,val)
#     sig.Write()

# Make a histogram of total signal
dummy = histos_TH2['SR_pass']['data_obs']
SigTot = dummy.Clone('SigTot')
SigTot.Reset()
for y in ['16','16APV','17','18']:
    SigTot.Add(histos_TH2['SR_pass'][f'NMSSM-XHY-1200-900_{y}'])
# Now zero out the values outside the region general region so the plot doesn't look atrocious
for i in range(1,SigTot.GetNbinsX()+1):
    for j in range(1, SigTot.GetNbinsY()+1):
        if (i<4) and (j<6):
            SigTot.SetBinContent(i,j,0.0)
        elif (j>9):
            SigTot.SetBinContent(i,j,0.0)
        elif (i>7):
            SigTot.SetBinContent(i,j,0.0)
SigTot.Write()

out.Close()

TEST = ROOT.TFile.Open('SHAPES.root','RECREATE')
TEST.cd()
for k,h in histos_TH2['SR_pass'].items():
    h.Write()
TEST.Close()

# Use uproot to read the TH2s
f = 'PostfitDistributions_SR_pass.root'
data = uproot.open(f)['data_obs']
bkg  = uproot.open(f)['TotalBkg']
Bunc = uproot.open(f)['BkgUnc']
Dunc = uproot.open(f)['DataUnc'] 
sig  = uproot.open(f)['SigTot']

data, binX, binY = data.to_numpy()
bkg, binX, binY  = bkg.to_numpy()
Dunc, binX, binY  = Dunc.to_numpy()
Bunc, binX, binY  = Bunc.to_numpy()

print(binX)
print(binY)

sig_tot, binX, binY = sig.to_numpy()
sig_tot = sig_tot * 14 # scale by S+B r value

################################################################
fig,ax=plt.subplots()
hep.hist2dplot(sig_tot, binX, binY, ax=ax, flow=None, labels=False)
fig.savefig('TEST.png')
################################################################

data_minus_bkg = data - bkg
sigma = np.sqrt(Dunc**2 + Bunc**2)
pull = data_minus_bkg / sigma


# Plot signal contours
sig_hist = sig_tot / sigma
levels = np.array([0.05, 0.5, 0.95]) * np.max(sig_hist)

# Create interpolated grid with 4x more points
x = np.array([(binX[i] + binX[i + 1]) / 2 for i in range(len(binX) - 1)])
y = np.array([(binY[i] + binY[i + 1]) / 2 for i in range(len(binY) - 1)])
x_interp = np.linspace(x.min(), x.max(), len(x) * 4)
y_interp = np.linspace(y.min(), y.max(), len(y) * 4)

# Interpolate signal histogram with increased smoothing
sig_interp = scipy.interpolate.RectBivariateSpline(
    y, x, sig_tot.T, s=8.
)  # Added smoothing parameter

print(sig_interp)

# Use edges instead of centers for interpolation range
x_edges = binX #np.array([1000.,1100.,1200.,1300.,1600.])#binX
y_edges = binY #np.array([700., 800.,  900., 1000., 1500.])#binY
x_interp = np.linspace(x_edges[0], x_edges[-1], len(x) * 4)
y_interp = np.linspace(y_edges[0], y_edges[-1], len(y) * 4)
X, Y = np.meshgrid(x_interp, y_interp)
Z = sig_interp(y_interp, x_interp)

# the signal interpolation (Z) looks really weird, so mask off some areas
rows = Z.shape[0]
cols = Z.shape[1]
row_mask = []
col_mask = []
print(rows,cols)
for i in range(rows):
    if i < 3:
        row_mask.append(True)
    elif i > 10:
        row_mask.append(True)
    else:
        row_mask.append(False)
for j in range(cols):
    if j < 3:
        col_mask.append(True)
    elif j > 7:
        col_mask.append(True)
    else:
        col_mask.append(False)
row_mask = np.array(row_mask)
col_mask = np.array(col_mask)
mask = np.empty(Z.shape,dtype=bool)
for i, row in enumerate(row_mask):
    for j, col in enumerate(col_mask):
        if row or col:
            mask[i,j] = True
        else:
            mask[i,j] = False
Z[mask] = 0.0

################################################################
fig,ax=plt.subplots()
hep.hist2dplot(Z, ax=ax, flow=None, labels=False)
fig.savefig('Z.png')
###############################################################


plt.style.use([hep.style.CMS])
fig, ax = plt.subplots(figsize=(12, 12),dpi=300)

ax.tick_params(axis='x', labelrotation=45)
ax.set_xlabel(r'$m_{X}^{rec}$ [GeV]')
ax.set_ylabel(r'$m_{Y}^{rec}$ [GeV]')

# 2D Pull plot
#hep.hist2dplot(pull, binX, binY, ax=ax, flow=None, labels=False)
h2d = hep.hist2dplot(pull, binX, binY, cmap="viridis", ax=ax) # cmin=-3.5, cmax=3.0,
h2d.cbar.set_label(r"(Data - Bkg.) / $\sigma$")
h2d.pcolormesh.set_edgecolor("face")

sig_colour = '#bd1f01'

cs = ax.contour(
    X,
    Y,
    Z,
    levels=levels,
    colors=sig_colour,
    # linestyles=["--", "-", "--"],
    linewidths=3,
)
ax.clabel(cs, cs.levels, inline=True, fmt="%.2f", fontsize=12)

# Add legend for signal contours
handles, labels = ax.get_legend_handles_labels()
# Create proxy artist for contour lines
contour_proxy = plt.Line2D([], [], color=sig_colour, linestyle="-", linewidth=3)
handles.append(contour_proxy)
labels.append(r'$X[1200]\to HY[900]$ / $\sigma$')
ax.legend(
    handles,
    labels,
    loc="upper right",
    bbox_to_anchor=(1.0, 0.98),  # Moved down from default 1.0
    fontsize=24,
    frameon=False,
)

add_cms_label(ax, "all", label=None, data=True, loc=2)

ax.text(
    0.35,
    0.92,
    'SR SP',
    transform=ax.transAxes,
    fontsize=24,
    fontproperties="Tex Gyre Heros:bold",
)

fig.savefig(f'postfit2Dpulls.png')
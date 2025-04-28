import ROOT
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
import os

# Full signal list
mxs = np.array([240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000])
mys = np.array([60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800])

# Only signals used in semi-boosted
mxs = np.array([800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000])
mys = np.array([300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800])


# len(MY) rows, len(MX) cols
sig_arr = np.empty((len(mys),len(mxs)))

# Fill the significance array
for i, my in enumerate(mys[::-1]):
    for j, mx in enumerate(mxs):
        if (my+125 > mx):
            sig_arr[i,j] = np.nan #-1.0
        else:
            s = f'../{mx}-{my}_fits/Unblinded_0x0/higgsCombine.Significance.mH125.123456.root'
            if not os.path.exists(s):
                sig_arr[i,j] = 0.0 #np.nan
            else:
                f = ROOT.TFile.Open(s)
                limit = f.Get('limit')
                if not limit:
                    #print(f'No significance for ({mx},{my})')
                    sig_arr[i,j] = 0.0 #np.nan #-3.0
                else:
                    limit.Scan()
                    sig_arr[i,j] = limit.limit
                    #print(limit.limit)

'''
# Make the significance plot
plt.style.use([hep.style.CMS])
fig, ax = plt.subplots(figsize=(20, 20))
hep.hist2dplot(sig_arr.T, mxs, mys, ax=ax, flow=None, shading='nearest', cmap='viridis')
'''

fig, ax = plt.subplots(figsize=(20,20))
sigs = ax.imshow(sig_arr, cmap='viridis')

for (i, j), z in np.ndenumerate(sig_arr):
    if not np.isnan(z):
        ax.text(j, i, '{0:.1f}'.format(z), ha='center', va='center', size=12)
    
plt.xticks(np.arange(len(mxs)), mxs)
plt.yticks(np.arange(len(mys)), mys[::-1])
cbar = fig.colorbar(sigs, ax=ax, label=r'Significance ($\sigma$)')
cbar.minorticks_on()

ax.set_xlabel(r'$m_{X}^{rec}$ [GeV]')
ax.set_ylabel(r'$m_{Y}^{rec}$ [GeV]')
ax.set_title(r'Significance')

fig.savefig('sig_2D.png')
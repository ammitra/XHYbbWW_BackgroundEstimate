'''
Script to plot the ratio of Pass/Fail data in SR as a function of MX and MY. In response to ARC comment:
"L192 This 0-order is an unusual and surprising result, it would be good to be supported with some plot of the data in two regions vs the two Variable."
'''
import ROOT, uproot 
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
from helpers import *
import os
from PyHist import PyHist

# Create TH2s and save to root file for uproot
input_file = '../B2G_unblinding/largest_significance_1200-900_postfit/Unblinded_0x0/postfitshapes_b.root'

procs = ['data_obs']
histos_TH2 = {}

histos_TH2['SR_pass'] = get_hists(input_file,'SR_pass',procs,prefit=False)
histos_TH2['SR_fail'] = get_hists(input_file,'SR_fail',procs,prefit=False)

out = ROOT.TFile.Open('PostfitDistributions.root','RECREATE')
out.cd()

for region in ['SR_fail','SR_pass']:
    for k,v in histos_TH2[region].items():
        for axis in ['X','Y']:
            # Get the projection
            proj = getattr(v,f'Projection{axis}')()

            proj.SetName(f'{k}_{region}_{axis}')
            proj.SetTitle(f'{k}_{region}_{axis}')
            proj.Write()

out.Close()

# Get the histograms of each projection
fname = 'PostfitDistributions.root'
rfile = ROOT.TFile.Open(fname)
for proj in ['X','Y']:
    for normalize in [True, False]:
        '''
        f = uproot.open(fname)[f'data_obs_SR_fail_{proj}']
        p = uproot.open(fname)[f'data_obs_SR_pass_{proj}']

        f, bins = f.to_numpy()
        p, bins = p.to_numpy()

        if normalize:
            f = f / f.sum()
            p = p / p.sum()

        p_by_f = p / f
        '''

        f = rfile.Get(f'data_obs_SR_fail_{proj}')
        p = rfile.Get(f'data_obs_SR_pass_{proj}')

        f = PyHist(f)
        p = PyHist(p)

        f.divide_by_bin_width()
        p.divide_by_bin_width()

        if normalize:
            f.bin_values = f.bin_values / f.bin_values.max()
            p.bin_values = p.bin_values / p.bin_values.max()

        bins = f.bin_edges

        p_by_f = p.bin_values / f.bin_values

        # Make the plot
        plt.style.use([hep.style.CMS])
        fig, (ax, rax) = plt.subplots(
            2, 1, figsize=(12, 14), gridspec_kw={"height_ratios": [3, 1], "hspace": 0.1}, sharex=True
        )

        hep.histplot(f.bin_values, bins, ax=ax, histtype='step', label='Data Fail', color='red')
        hep.histplot(p.bin_values, bins, ax=ax, histtype='step', label='Data Pass', color='blue')

        hep.histplot(p_by_f, bins, ax=rax, histtype='step', color='black')

        # centers = p.get_bin_centers()
        # xerr = [width / 2 for width in p.bin_widths]
        # rax.errorbar(x=centers, y=p_by_f, xerr=xerr, color='black', ls='none')

        if normalize: 
            ax.set_title('Normalized data distributions - SR Pass / SR Fail')
            ax.set_ylabel('A.U.')
            rax.set_ylim(0.,2.)
            rax.hlines(y=1, xmin=bins[0], xmax=bins[-1], linewidth=2, color='gray', linestyle='dashed')
        else:
            ax.set_yscale('log')
            ax.set_ylabel('Events/bin')
            ax.set_title('Data distributions - SR Pass / SR Fail')

        rax.set_xlabel(r'$M_{%s}^{rec}$ [GeV]'%proj)
        rax.set_ylabel('Pass/Fail')

        ax.legend(loc='best')

        fig.savefig(f'PF_ratio_data_M{proj}{"_normalized" if normalize else ""}.png')

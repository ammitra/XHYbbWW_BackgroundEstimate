import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from collections import OrderedDict
import array
import subprocess
from TwoDAlphabet.binning import convert_to_events_per_unit, get_min_bin_width

# Options for plotting
stack_style = {
    'edgecolor': (0, 0, 0, 0.5),
}
errorbar_style = {
    'linestyle': 'none',
    'marker': '.',      # display a dot for the datapoint
    'elinewidth': 2,    # width of the errorbar line
    'markersize': 20,   # size of the error marker
    'capsize': 0,       # size of the caps on the errorbar (0: no cap fr)
    'color': 'k',       # black 
}

# Function stolen from https://root-forum.cern.ch/t/trying-to-convert-rdf-generated-histogram-into-numpy-array/53428/3
def hist2array(hist, include_overflow=False, return_errors=False):
    '''Create a numpy array from a ROOT histogram without external tools like root_numpy.

    Args:
        hist (TH1): Input ROOT histogram
        include_overflow (bool, optional): Whether or not to include the under/overflow bins. Defaults to False. 
        return_errs (bool, optional): Whether or not to return an array containing the sum of the weights squared. Defaults to False.

    Returns:
        arr (np.ndarray): Array representing the ROOT histogram
        errors (np.ndarray): Array containing the sqrt of the sum of weights squared
    '''
    hist.BufferEmpty()
    root_arr = hist.GetArray()
    if isinstance(hist, ROOT.TH1):
        shape = (hist.GetNbinsX() + 2,)
    elif isinstance(hist, ROOT.TH2):
        shape = (hist.GetNbinsY() + 2, hist.GetNbinsX() + 2)
    elif isinstance(hist, ROOT.TH3):
        shape = (hist.GetNbinsZ() + 2, hist.GetNbinsY() + 2, hist.GetNbinsX() + 2)
    else:
        raise TypeError(f'hist must be an instance of ROOT.TH1, ROOT.TH2, or ROOT.TH3')

    # Get the array and, optionally, errors
    arr = np.ndarray(shape, dtype=np.float64, buffer=root_arr, order='C')
    if return_errors:
        errors = np.sqrt(np.ndarray(shape, dtype='f8', buffer=hist.GetSumw2().GetArray()))

    if not include_overflow:
        arr = arr[tuple([slice(1, -1) for idim in range(arr.ndim)])]
        if return_errors:
            errors = errors[tuple([slice(1, -1) for idim in range(errors.ndim)])]

    if return_errors:
        return arr, errors
    else:
        return arr


def poisson_conf_interval(k):
    """
    Calculate Poisson (Garwood) confidence intervals using ROOT's TH1 with kPoisson error option.
    
    Parameters:
    k (array): The number of counts (events) per bin.

    Returns:
    lower (array): Bin count - lower error.
    upper (array): Bin count + upper error.
    """
    lower = np.zeros_like(k, dtype=float)
    upper = np.zeros_like(k, dtype=float)
    #Temp hist to exploit ROOT's built-in CI calculating function
    hist = ROOT.TH1F("hist_delete", "", 1, 0, 1)
    hist.SetBinErrorOption(ROOT.TH1.kPoisson)
    hist.Sumw2()

    for i, count in enumerate(k):
        hist.SetBinContent(1, count)
        
        lower[i] = hist.GetBinContent(1) - hist.GetBinErrorLow(1)
        upper[i] = hist.GetBinContent(1) + hist.GetBinErrorUp(1)
        
    hist.Delete()
    
    return lower, upper    

def plot_stack(
    outname,
    data = None, # numpy array
    bkgs = {},  # {latex name : (numpy array, color)} ordered by yield - use OrderedDict
    sigs = {},  # {latex name : (numpy array, color)}
    edges = None,
    title = '',
    xtitle = '',
    ytitle ='',
    subtitle = '',
    totalBkg = None,
    logyFlag = False,
    lumiText = r'$138 fb^{-1} (13 TeV)$',
    extraText = 'Preliminary',
    units='GeV'):

    plt.style.use([hep.style.CMS])
    fig, (ax, rax) = plt.subplots(
        2, 1, figsize=(12, 10), dpi=100, gridspec_kw={"height_ratios": [3, 1], "hspace": 0.1}, sharex=True
    )

    bkg_stack = np.vstack([val[0] for key, val in bkgs.items()])
    bkg_stack = np.hstack([bkg_stack, bkg_stack[:,-1:]])
    bkg_stack = np.hstack([bkg_stack])
    bkg_colors = [val[1] for key, val in bkgs.items()]
    bkg_labels = [key for key, val in bkgs.items()]

    sig_stack = np.vstack([val[0] for key, val in sigs.items()])
    sig_stack = np.hstack([sig_stack, sig_stack[:,-1:]])
    sig_stack = np.hstack([sig_stack])
    sig_colors = [val[1] for key, val in sigs.items()]
    sig_labels = [key for key, val in sigs.items()]


    ax.stackplot(edges, bkg_stack, labels=bkg_labels, colors=bkg_colors, step='post', **stack_style)
    ax.set_ylabel(f'Events / bin width $(GeV^{-1})$')
    ax.set_ylabel(ytitle)
    
    # plot data 
    print(outname)
    print(data)
    lower_errors, upper_errors = poisson_conf_interval(data)
    yerr = [data - lower_errors, upper_errors - data]
    bin_centers = (edges[:-1] + edges[1:])/2
    ax.errorbar(x=bin_centers, y=data, yerr=np.abs(yerr), xerr=None, label='Data', **errorbar_style)

    # plot signals
    for key,val in sigs.items():
        sigarr = val[0] #/ bin_widths
        scaling = 1.0
        ax.step(x=edges, y=np.hstack([sigarr,sigarr[-1]])*scaling, where='post', color=val[1], label=r'%s $\times$ %s'%(key,round(scaling,1)))
    
    if logyFlag:
        if totalBkg.max() >= data.max():
            ax.set_ylim(0.001, totalBkg.max()*1e5)
        else:
            ax.set_ylim(0.001, data.max()*1e5)
        ax.set_yscale('log')
    else:
        if totalBkg.max() >= data.max():
            ax.set_ylim(0, totalBkg.max()*1.5)
        else:
            ax.set_ylim(0, data.max()*1.5)

    ax.legend(loc='best')
    ax.margins(x=0)
    hep.cms.label(loc=0, ax=ax, label=extraText, rlabel='', data=True)
    hep.cms.lumitext(lumiText,ax=ax)

    # now plot ratio of data/prediction
    bkg_nonzero = totalBkg.copy()
    bkg_nonzero[bkg_nonzero==0] = 1e-2
    data_over_pred = data / bkg_nonzero
    rax.set_ylim([0, 2])
    hep.histplot(data_over_pred, edges, histtype='errorbar', color='black', ax=rax)
    rax.set_ylabel('Data/Bkg.')
    rax.margins(x=0)
    rax.grid(axis='y')
    ax.set_xlabel(xtitle)


    plt.savefig(outname)

def getProjn(h,proj):
    hprojn = getattr(h,f'Projection{proj}')()
    hprojn.SetDirectory(0)
    return hprojn

f = ROOT.TFile.Open('1800-1200_fits/NMSSM-XHY-1800-1200-SR1x0-VR1x0_area/plots_fit_b/all_plots.root','READ')

prefit_hists  = [i.GetName() for i in f.GetListOfKeys() if ('prefit_2D' in i.GetName())]
postfit_hists = [i.GetName() for i in f.GetListOfKeys() if ('postfit_2D' in i.GetName())]

# get test histograms for X and Y projections
dummyH = f.Get(prefit_hists[0]).Clone()

dummyX = dummyH.ProjectionX(); dummyX.Reset(); dummyX = hist2array(dummyX)
dummyY = dummyH.ProjectionY(); dummyY.Reset(); dummyY = hist2array(dummyY)

binningX = np.array([800,900,1000,1100,1200,1300,1400,1600,2000,3000,4500])
binningY = np.array([300,400,500,600,700,800,900,1000,1500,2000,3000,4500])

for time, histlist in {'prefit':prefit_hists, 'postfit':postfit_hists}.items():
    for region in ['VR_fail', 'VR_pass']:
        for proj in ['X','Y']:

            tt   = [np.zeros_like(dummyX if proj == 'X' else dummyY),'red']
            wj   = [np.zeros_like(dummyX if proj == 'X' else dummyY),'green']
            zj   = [np.zeros_like(dummyX if proj == 'X' else dummyY),'blue']
            xy   = [np.zeros_like(dummyX if proj == 'X' else dummyY),'black']
            st   = [np.zeros_like(dummyX if proj == 'X' else dummyY),'purple']
            qcd  = [np.zeros_like(dummyX if proj == 'X' else dummyY),'yellow']
            data = [np.zeros_like(dummyX if proj == 'X' else dummyY),'black']
            tot  = [np.zeros_like(dummyX if proj == 'X' else dummyY),'black']

            for histname in histlist:
                if region not in histname: continue

                h = f.Get(histname)
                h = getProjn(h,proj)
                min_width = get_min_bin_width(h)
                h = convert_to_events_per_unit(h)
                h = hist2array(h)
                    
                if 'ttbar' in histname:
                    tt[0] += h
                elif 'WJets' in histname:
                    wj[0] += h
                elif 'ZJets' in histname:
                    zj[0] += h
                elif 'NMSSM' in histname:
                    xy[0] += h
                elif 'ST' in histname:
                    st[0] += h
                elif 'Background' in histname:
                    qcd[0] += h
                elif 'data' in histname:
                    data[0] += h
                elif 'Total' in histname:
                    tot[0] += h

            bkgHists = OrderedDict(
                [
                    (r'QCD',qcd),
                    (r'$t\bar{t}$',tt),
                    (r'W+Jets',wj),
                    (r'Z+Jets',zj),
                    (r'Single-top',st)
                ]
            )
            sigHists = OrderedDict([(r'$X_{1800}, Y_{1200}$',xy)])

            xtitle = r'$m_{X}$ [GeV]' if proj == 'X' else r'$m_{Y}$ [GeV]'
            print(f'Plotting {region} {time} projection {proj}')
            plot_stack(
                outname=f'plots/{region}_{time}_projection{proj}.png',
                data=data[0],
                bkgs=bkgHists,
                sigs=sigHists,
                totalBkg=tot[0],
                edges=binningX if proj == 'X' else binningY,
                title=f'{region}_{time}_proj{proj}',
                xtitle=xtitle,
                ytitle=f'Events / {min_width} GeV',
                lumiText=r'$138 fb^{-1}$ (13 TeV)',
                extraText='Work in progress'
            )

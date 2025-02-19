'''
Based off Matej's work
https://github.com/Boosted-X-H-bb-Y-anomalous-jet/AnomalousSearchPlotting/blob/master/plots_for_paper.py
'''
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import ROOT as r
plt.style.use(hep.style.CMS)
from PyHist import PyHist
import copy
import matplotlib

errorbar_style = {
    'linestyle': 'none',
    'marker': '.',      # display a dot for the datapoint
    'elinewidth': 2,    # width of the errorbar line
    'markersize': 20,   # size of the error marker
    #'capsize': 4,       # size of the caps on the errorbar (0: no cap fr)
    'color': 'k',       # black 
}

stack_style = {
    'edgecolor': (0, 0, 0, 0.5),
}

hatch_style = {
    'facecolor': 'none',
    'edgecolor': '#9c9ca1',
    'alpha': 0.1,
    'linewidth': 0,
    'hatch': '//',
}



def get_binning_x(hLow,hSig,hHigh):
    bins = []
    for i in range(1,hLow.GetNbinsX()+1):
        bins.append(hLow.GetXaxis().GetBinLowEdge(i))
    for i in range(1,hSig.GetNbinsX()+1):
        bins.append(hSig.GetXaxis().GetBinLowEdge(i))
    for i in range(1,hHigh.GetNbinsX()+2):#low edge of overflow is high edge of last bin
        bins.append(hHigh.GetXaxis().GetBinLowEdge(i))
    bins = np.array(bins,dtype='float64')
    return bins

def get_binning_y(hLow,hSig,hHigh):
    #histos should have same binning in Y
    bins = []
    for i in range(1,hLow.GetNbinsY()+2):
        bins.append(hLow.GetYaxis().GetBinLowEdge(i))
    bins = np.array(bins,dtype='float64')
    return bins

def get2DPostfitPlot(file, process, region, prefit=False):
    if not r.TFile.Open(file):
        raise FileNotFoundError(f"The file '{file}' does not exist or cannot be opened.")
    
    f = r.TFile.Open(file)
    fitStatus = "prefit" if prefit else "postfit"
    
    hLow = f.Get(f"{region}_LOW_{fitStatus}/{process}")
    if not hLow:
        raise ValueError(f"Histogram '{region}_LOW_{fitStatus}/{process}' does not exist in the file '{file}'.")
    
    hSig = f.Get(f"{region}_SIG_{fitStatus}/{process}")
    if not hSig:
        raise ValueError(f"Histogram '{region}_SIG_{fitStatus}/{process}' does not exist in the file '{file}'.")
    
    hHigh = f.Get(f"{region}_HIGH_{fitStatus}/{process}")
    if not hHigh:
        raise ValueError(f"Histogram '{region}_HIGH_{fitStatus}/{process}' does not exist in the file '{file}'.")
    
    h2 = merge_low_sig_high(hLow, hSig, hHigh, hName=f"h2_{process}_{region}")
    h2.SetDirectory(0)
    return h2


def merge_low_sig_high(hLow,hSig,hHigh,hName="temp"):
    n_x_low     = hLow.GetNbinsX()
    n_x_sig     = hSig.GetNbinsX()
    n_x_high    = hHigh.GetNbinsX()
    n_x         = n_x_low + n_x_sig + n_x_high
    n_y         = hLow.GetNbinsY()#assumes Y bins are the same
    bins_x      = get_binning_x(hLow,hSig,hHigh)
    bins_y      = get_binning_y(hLow,hSig,hHigh)
    h_res       = r.TH2F(hName,"",n_x,bins_x,n_y,bins_y)
    for i in range(1,n_x_low+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+0,j,hLow.GetBinContent(i,j))
            h_res.SetBinError(i+0,j,hLow.GetBinError(i,j))

    for i in range(1,n_x_sig+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+n_x_low,j,hSig.GetBinContent(i,j))
            h_res.SetBinError(i+n_x_low,j,hSig.GetBinError(i,j))

    for i in range(1,n_x_high+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+n_x_sig+n_x_low,j,hHigh.GetBinContent(i,j))
            h_res.SetBinError(i+n_x_sig+n_x_low,j,hHigh.GetBinError(i,j))
    return h_res

def get_hists(input_file,region,processes):
    histos_region_dict = {}
    for process in processes:
        h2 = get2DPostfitPlot(input_file,process,region)
        histos_region_dict[process]=h2
    return histos_region_dict

def calcRatio(hData,hMC,dataErrs):
    ratioVals=[]
    ratioErrs = copy.deepcopy(dataErrs)
    for i in range(len(hData)):
        # print(hData)
        # print(hData.get_error_pairs()[0][0])
        data      = hData[i]
        mc        = hMC[i]
        ratioVal     = data/(mc+0.000001)#Protect division by zero
        ratioErrs[0][i] = ratioErrs[0][i]/(mc+0.000001)
        ratioErrs[1][i] = ratioErrs[1][i]/(mc+0.000001)
        ratioVals.append(ratioVal)

    return ratioVals, ratioErrs

def calcSystBand(hMC,uncBand):
    systBand = [[],[]]
    for i in range(len(hMC)):
        systBandUp = uncBand[0][i]/hMC[i]
        systBandDn = uncBand[1][i]/hMC[i]
        systBand[0].append(1+systBandUp)
        systBand[1].append(1-systBandDn)
    return systBand

def calcPulls(hData,hMC,dataErrs,uncBand):
    pulls = []
    for i in range(len(hMC)):
        num = hData[i]-hMC[i]
        if(num>0):
            err_data = dataErrs[0][i]#error low
            err_mc = uncBand[1][i]#error high
        else:
            err_data = dataErrs[1][i]
            err_mc = uncBand[0][i]
        den = np.sqrt(err_data**2+err_mc**2)
        if(den==0):
            den = 0.0000000001#Avoid division by zero
        pull = num/den
        pulls.append(pull)
    return pulls


colours = {
    # CMS 10-colour-scheme from
    # https://cms-analysis.docs.cern.ch/guidelines/plotting/colors/#categorical-data-eg-1d-stackplots
    "darkblue": "#3f90da",
    "lightblue": "#92dadd",
    "orange": "#e76300",
    "red": "#bd1f01",
    "darkpurple": "#832db6",
    "brown": "#a96b59",
    "gray": "#717581",
    "beige": "#b9ac70",
    "yellow": "#ffa90e",
    "lightgray": "#94a4a2",
    # extra colours
    "darkred": "#A21315",
    "green": "#7CB518",
    "mantis": "#81C14B",
    "forestgreen": "#2E933C",
    "darkgreen": "#064635",
    "purple": "#9381FF",
    "deeppurple": "#36213E",
    "ashgrey": "#ACBFA4",
    "canary": "#FFE51F",
    "arylideyellow": "#E3C567",
    "earthyellow": "#D9AE61",
    "satinsheengold": "#C8963E",
    "flax": "#EDD382",
    "vanilla": "#F2F3AE",
    "dutchwhite": "#F5E5B8",
}
BG_COLOURS = {
    "QCD": "darkblue",
    "TT": "brown",
    "W+Jets": "orange",
    "Z+Jets": "yellow"
}

def ARC_plot(hData,hMC,hTotalBkg,labelsMC,colorsMC,xlabel,outputFile,xRange=[],yRange=[],projectionText="",yRangeLog=[]):
    # Set up variables
    edges = hData.bin_edges
    centersData = hData.get_bin_centers()

    # K:V {label:color}
    label_colors = dict(zip(labelsMC,colorsMC))

    # Concatenate processes per year (and W+Z -> V)
    tt  = np.zeros_like(hData.bin_values)
    wj  = np.zeros_like(hData.bin_values)
    zj  = np.zeros_like(hData.bin_values)
    xy  = np.zeros_like(hData.bin_values)
    qcd = np.zeros_like(hData.bin_values)

    for h in hMC:
        hname = h.histo_name
        if 'ttbar_' in hname:
            tt += h.bin_values
        elif 'WJets' in hname:
            wj += h.bin_values
        elif 'ZJets' in hname:
            zj += h.bin_values
        elif 'NMSSM' in hname:
            xy += h.bin_values
        elif 'Background' in hname:
            qcd += h.bin_values
        else:
            continue

    # Set up plotting 
    plt.style.use([hep.style.CMS])
    fig, (ax, rax) = plt.subplots(
        2, 1, figsize=(12, 14), gridspec_kw={"height_ratios": [3, 1], "hspace": 0}, sharex=True
    )

    # Organize backgrounds in opposite order of yields (lowest first)
    bkg_yields = np.array([wj, zj, tt, qcd])
    bkg_colors = ["#e76300","#ffa90e","#a96b59","#3f90da"]
    bkg_labels = ['W+jets','Z+jets',r'$t\bar{t}$','QCD']
    # Organize signal
    sig_yields = xy
    sig_colors = "#bd1f01"
    sig_scale  = 1
    sig_labels = r'$X[1800]\to HY[1200]\times %s$'%(sig_scale)
    # Organize data
    yerr = hData.get_error_pairs()
    xerrorsData = [width / 2 for width in hData.bin_widths]
    # Organize uncertainty
    tot_err = hTotalBkg.get_error_pairs()
    y1 = bkg_yields.sum(axis=0) - tot_err[0]
    y2 = bkg_yields.sum(axis=0) + tot_err[1]

    # Plot backgrounds
    hep.histplot(bkg_yields, edges, ax=ax, stack=True, label=bkg_labels, histtype="fill",facecolor=bkg_colors)
    # Plot signal 
    ax.step(x=edges, y=np.hstack([sig_yields,sig_yields[-1]])*sig_scale, where='post', label=sig_labels, color=sig_colors, linewidth=3)
    # Plot data 
    ax.errorbar(x=centersData, y=hData.bin_values, xerr=xerrorsData, yerr=yerr, label='Data', capsize=0, **errorbar_style)
    # Plot systematic uncertainty
    ax.fill_between(x=edges, y1=np.hstack([y1,y1[-1]]), y2=np.hstack([y2,y2[-1]]), step='post', label=r'Total Bkg. Uncertainty', **hatch_style)

    # Ratio plot
    def calcRatio(hData,hMC,dataErrs):
        ratioVals=[]
        ratioErrs = copy.deepcopy(dataErrs)
        for i in range(len(hData)):
            data      = hData[i]
            mc        = hMC[i]
            ratioVal     = data/(mc+0.000001)#Protect division by zero
            ratioErrs[0][i] = ratioErrs[0][i]/(mc+0.000001)
            ratioErrs[1][i] = ratioErrs[1][i]/(mc+0.000001)
            ratioVals.append(ratioVal)
        return ratioVals, ratioErrs
    def calcSystBand(hMC,uncBand):
        systBand = [[],[]]
        for i in range(len(hMC)):
            systBandUp = uncBand[0][i]/hMC[i]
            systBandDn = uncBand[1][i]/hMC[i]
            systBand[0].append(1+systBandUp)
            systBand[1].append(1-systBandDn)
        return systBand
    ratioVals, ratioErrs = calcRatio(hData.bin_values,hTotalBkg.bin_values,hData.get_error_pairs())
    systBand = calcSystBand(hTotalBkg.bin_values,hTotalBkg.get_error_pairs())
    systBand_lower = list(systBand[0]) + [systBand[0][-1]]
    systBand_upper = list(systBand[1]) + [systBand[1][-1]]
    # Plot
    rax.errorbar(x=centersData, y=ratioVals, xerr=xerrorsData, yerr=ratioErrs, label=r'Data/Bkg.', capsize=4, **errorbar_style)
    rax.fill_between(x=edges, y1=systBand_lower, y2=systBand_upper, label=r'$\sigma_{syst}/\sigma_{stat}$', step='post', **hatch_style)


    # To match Raghav we want the legend to be in order: Data, signal, [QCD,TT,ZJ,WJ], syst unc
    handles, labels = ax.get_legend_handles_labels()
    # print(handles)
    # print(labels)
    # exit()
    order = [6,4,3,2,1,0,5]
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc='best',ncol=1, fontsize='medium')

    # Format Axes
    yMaximum = max(hData.bin_values)*1.5
    ax.set_ylim([0., yMaximum])
    ax.margins(x=0)
    rax.set_ylim([0,2])
    rax.margins(x=0)
    lumiText = r"138 $fb^{-1}$ (13 TeV)"    
    hep.cms.lumitext(lumiText,ax=ax)
    hep.cms.label(loc=2, ax=ax, label='Preliminary', rlabel='', data=True)
    rax.set_xlabel(xlabel, fontsize=32)
    rax.set_ylabel('Data/Bkg.')
    ax.set_ylabel('Events / GeV')

    # Region naming
    if 'SR' in outputFile:
        if 'fail' in outputFile:
            region_text1 = r'SR Fail'
        else:
            region_text1 = r'SR Pass'
    else:
        if 'fail' in outputFile:
            region_text1 = r'VR Fail'
        else:
            region_text1 = r'VR Pass'

    ax.text(0.3, 0.95, region_text1, fontsize=30, va='top', ha='left', transform=ax.transAxes, fontproperties='Tex Gyre Heros:bold')

    # Reduce whitespace around figure and save
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
    plt.savefig(outputFile)


def plot_projection(histos_dict, region, processes, labels_dict, colors_dict, axis="X",yRange=[],yRangeLog=[1,10**5]):
    if axis not in ["X", "Y"]:
        raise ValueError("Invalid axis. Choose 'X' or 'Y'.")

    # Set up variables
    axis_label = "$M_{X}$ [GeV]" if axis == "X" else "$M_{Y}$ [GeV]"
    file_suffix = "mX" if axis == "X" else "mY"
    x_range = [800,4500] if axis == "X" else [300,4500]
    projection_method = f"Projection{axis}"

    # Extract histograms
    histos = histos_dict[region]

    h_data = getattr(histos["data_obs"], projection_method)(f"data_{axis}")
    h_data.SetBinErrorOption(1)
    h_data = PyHist(h_data)
    h_data.divide_by_bin_width()

    h_mc = []
    labels_mc = []
    colors_mc = []
    for process in processes:
        h_temp = getattr(histos[process], projection_method)(f"{process}_{axis}")
        h_temp = PyHist(h_temp)
        h_name = h_temp.histo_name
        h_temp.divide_by_bin_width()
        h_mc.append(h_temp)
        labels_mc.append(labels_dict[process])
        colors_mc.append(colors_dict[process])

    h_bkg = getattr(histos["TotalBkg"], projection_method)(f"bkg_{axis}")
    h_bkg = PyHist(h_bkg)
    h_bkg.divide_by_bin_width()

    ARC_plot(h_data, h_mc, h_bkg,labels_mc, colors_mc,axis_label,f"B2G_unblinding/postfit_distributions/{region}_{file_suffix}.pdf",xRange=x_range,yRange=yRange,projectionText=region.replace("_", " "),yRangeLog=yRangeLog)

if __name__ == "__main__":
    input_file = "B2G_unblinding/Unblinded_0x0/postfitshapes_b.root"

    proc_base = ['WJets','ZJets','NMSSM-XHY-1800-1200','ttbar']
    procs = []
    for p in proc_base:
        for y in ['16APV','16','17','18']:
            procs.append(f'{p}_{y}')

    procs_SR_pass = procs + ['Background_SR_pass_0x0','data_obs','TotalBkg']
    procs_SR_fail = procs + ['Background_SR_fail','data_obs','TotalBkg']

    histos_dict = {}
    histos_dict['SR_fail'] = get_hists(input_file,'SR_fail',procs_SR_fail)
    histos_dict['SR_pass'] = get_hists(input_file,'SR_pass',procs_SR_pass)


    labels_dict = {}
    colors_dict = {}
    for key in procs_SR_pass + procs_SR_fail:
        if key in labels_dict: continue 
        if key in colors_dict: continue
        else:
            if 'WJets' in key:
                label = '__nolabel__'
                color = '#1f77b4'
            elif 'ZJets' in key:
                label = 'V+Jets'
                color = '#1f77b4'
            elif 'ttbar' in key:
                label = r'$t\bar{t}$'
                color = '#d42e12'
            elif 'Background' in key:
                label = 'Multijet'
                color = '#f39c12'
            elif 'Tprime' in key:
                label = r'$T^{\prime}_{1800} \to t\phi_{125}$'
                color = 'black'
            colors_dict[key] = color
            labels_dict[key] = label

    for k, v in {
        'SR_pass':procs_SR_pass,
        'SR_fail':procs_SR_fail
    }.items():
        for axis in ['X','Y']:
            plot_projection(histos_dict,k,v,labels_dict,colors_dict,axis=axis)
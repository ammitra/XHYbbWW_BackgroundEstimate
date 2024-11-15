import ROOT, time
def plot_gof(fit_dir, seed=123456):

    toyOutput = ROOT.TFile.Open(f'{fit_dir}/higgsCombineToys.GoodnessOfFit.mH125.{seed}.root','READ')
    toy_limit_tree = toyOutput.Get('limit')

    # Now to analyze the output
    # Get observation
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(True)
    gof_data_file = ROOT.TFile.Open(f'{fit_dir}/higgsCombineData.GoodnessOfFit.mH125.root','READ')
    gof_limit_tree = gof_data_file.Get('limit')
    gof_limit_tree.GetEntry(0)
    gof_data = gof_limit_tree.limit

    # Get toys
    toy_limit_tree.Draw('limit>>hlimit','limit>1.0 && limit<%s && limit != %s'%(gof_data*2.0,gof_data)) 
    htoy_gof = ROOT.gDirectory.Get('hlimit')
    time.sleep(1) # if you don't sleep the code moves too fast and won't perform the fit
    htoy_gof.Fit("gaus")

    # Fit toys and derive p-value
    gaus = htoy_gof.GetFunction("gaus")
    pvalue = 1-(1/gaus.Integral(-float("inf"),float("inf")))*gaus.Integral(-float("inf"),gof_data)

    # Write out for reference
    with open(f'{fit_dir}gof_results.txt','w') as out:
        out.write('Test statistic in data = '+str(gof_data))
        out.write('Mean from toys = '+str(gaus.GetParameter(1)))
        out.write('Width from toys = '+str(gaus.GetParameter(2)))
        out.write('p-value = '+str(pvalue))

    # Extend the axis if needed
    if htoy_gof.GetXaxis().GetXmax() < gof_data:
        print ('Axis limit greater than GOF p value')
        binwidth = htoy_gof.GetXaxis().GetBinWidth(1)
        xmin = htoy_gof.GetXaxis().GetXmin()
        new_xmax = int(gof_data*1.1)
        new_nbins = int((new_xmax-xmin)/binwidth)
        toy_limit_tree.Draw('limit>>hlimitrebin('+str(new_nbins)+', '+str(xmin)+', '+str(new_xmax)+')','limit>0.001 && limit<1500') 
        htoy_gof = ROOT.gDirectory.Get('hlimitrebin')
        htoy_gof.Fit("gaus")
        gaus = htoy_gof.GetFunction("gaus")

    # Arrow for observed
    arrow = ROOT.TArrow(gof_data,0.25*htoy_gof.GetMaximum(),gof_data,0)
    arrow.SetLineWidth(2)

    # Legend
    leg = ROOT.TLegend(0.1,0.7,0.4,0.9)
    leg.SetLineColor(ROOT.kWhite)
    leg.SetLineWidth(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.AddEntry(htoy_gof,"toy data","lep")
    leg.AddEntry(arrow,"observed = %.1f"%gof_data,"l")
    leg.AddEntry(0,"p-value = %.2f"%(pvalue),"")

    # Draw
    cout = ROOT.TCanvas('cout','cout',800,700)
    htoy_gof.SetTitle('')
    htoy_gof.Draw('pez')
    arrow.Draw()
    leg.Draw()

    cout.Print(f'{fit_dir}gof_plot.pdf','pdf')
    cout.Print(f'{fit_dir}gof_plot.png','png')

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-w', type=str, dest='workspace',
                        action='store', default='VR',
                        help='directory containing the GoF from data + toys')
    parser.add_argument('-s', type=str, dest='seed',
                        action='store', default='42',
                        help='seed used in toy generation')

    args = parser.parse_args()

    plot_gof(args.workspace, args.seed)
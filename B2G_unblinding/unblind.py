from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from TwoDAlphabet.helpers import make_env_tarball, cd, execute_cmd
from TwoDAlphabet.ftest import FstatCalc
import os

############################################################################
mask_VR = "mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1" 
freeze_VR = "var{Background_VR.*},rgx{Background_VR.*}"
set_VR = "var{Background_VR.*}=0,rgx{Background_VR.*}=0"
float_SR = "var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
main_dir = 'B2G_unblinding'
############################################################################


def _select_signal(row, args):
    signame = args[0]
    SR_poly_order = args[1]
    VR_poly_order = args[2]
    if row.process_type == 'SIGNAL':
        if signame in row.process:
            return True
        else:
            return False
    elif 'Background' in row.process:
        if row.process == 'Background_VR_fail':
            print(f'\tAdding {row.process} for tf {VR_poly_order} describing QCD in VR_fail')
            return True
        elif row.process == f'Background_VR_pass_{VR_poly_order}':
            print(f'\tAdding {row.process} for tf {VR_poly_order} describing QCD in VR_pass')
            return True
        elif row.process == f'Background_SR_fail':
            print(f'\tAdding {row.process} for tf {SR_poly_order} describing QCD in SR_fail')
            return True
        elif row.process == f'Background_SR_pass_{SR_poly_order}':
            print(f'\tAdding {row.process} for tf {SR_poly_order} describing QCD in SR_pass')
            return True
        else:
            return False
    else:
        return True

def make_card(tf=''):
    if os.path.isfile(f'{main_dir}/card_{tf}.txt'):
        print(f'Combine card already exists for (1800,1200), TF={tf}')
    else:
        twoD = TwoDAlphabet(main_dir, '{}/runConfig.json'.format(main_dir), loadPrevious=True)
        subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-1800-1200', tf, tf)
        working_area = f'Unblinded_{tf}'
        twoD.MakeCard(subset, working_area)
        execute_cmd(f'mv {main_dir}/{working_area}/card.txt {main_dir}/{working_area}/card_{tf}.txt')
        #execute_cmd(f'sed -i "s-../-./-g" {main_dir}/{working_area}/card_{tf}.txt')
        ws_command = f'text2workspace.py {main_dir}/{working_area}/card_{tf}.txt --channel-masks -o {main_dir}/{working_area}/initialFitWorkspace_{tf}.root'
        execute_cmd(ws_command)

def FitDiagnostics(tf='', strat=0, tol=0.1, robustFit=True, rMin=-1, rMax=1, verbosity=2):
    working_area = f'Unblinded_{tf}'
    with cd(f'{main_dir}/{working_area}'):
        if not os.path.isfile(f'card_{tf}.txt'):
            raise ValueError(f'card_{tf} does not exist. Create it first')
        else:
            print('FitDiagnostics (UNBLINDED)')
            execute_cmd('mkdir -p outs/')
            combine_command = f'(set -x; combine -M FitDiagnostics -m 120 -d initialFitWorkspace_{tf}.root --saveWorkspace --setParameters {mask_VR},{set_VR} --freezeParameters {freeze_VR} --rMin {rMin} --rMax {rMax} --cminDefaultMinimizerTolerance {tol} --cminDefaultMinimizerStrategy {strat} --robustFit {1 if robustFit else 0} --X-rtd MINIMIZER_MaxCalls=400000 --ignoreCovWarning -v {verbosity} --saveShapes --saveNormalizations --saveWithUncertainties --saveOverallShapes) 2>&1 | tee outs/FitDiagnostics_{tf}.txt'
            execute_cmd(combine_command)
            from TwoDAlphabet.twoDalphabet import make_postfit_workspace
            make_postfit_workspace('')

def PlotFit(tf):
    twoD = TwoDAlphabet(main_dir, '{}/runConfig.json'.format(main_dir), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-1800-1200', tf, tf)
    # customize the plots to include region definitions
    subtitles = {
        "VR_fail": r"VR Fail",
        "VR_pass": r"VR Pass",
        "SR_fail": r"SR Fail",
        "SR_pass": r"SR Pass"
    }
    regions = [['SR']]
    twoD.StdPlots(f'Unblinded_{tf}', subset, subtitles=subtitles, regionsToGroup=regions)


def FTest(poly1, poly2):
    def _gof_for_FTest(twoD, subtag, card_or_w='card.txt'):
        run_dir = twoD.tag+'/'+subtag
        with cd(run_dir):
            gof_data_cmd = [
                'combine -M GoodnessOfFit',
                '-d '+card_or_w,
                '--algo=saturated',
                '-n _gof_data',
                f'--freezeParameters {freeze_VR}',
                f'--setParameters {mask_VR},{set_VR}'
            ]
            gof_data_cmd = ' '.join(gof_data_cmd)
            execute_cmd(gof_data_cmd)
    # Do the F-test
    twoD = TwoDAlphabet(main_dir, '{}/runConfig.json'.format(main_dir), loadPrevious=True)
    binning = twoD.binnings['default']
    nBins = (len(binning.xbinList)-1)*(len(binning.ybinList)-1)
    # Params for poly 1
    print('######################## POLY 1 ########################\n')
    params1 = twoD.ledger.select(_select_signal, 'NMSSM-XHY-1800-1200', poly1, poly1).alphaParams
    rpfSet1 = params1[params1["name"].str.contains("rpf")]
    rpfSet1 = rpfSet1[~rpfSet1["owner"].str.contains("VR")]
    nRpfs1  = len(rpfSet1.index)
    print(f'nParams TF {poly1} : {nRpfs1}')
    print(rpfSet1)
    _gof_for_FTest(twoD, f'Unblinded_{poly1}', card_or_w=f'initialFitWorkspace_{poly1}.root')
    gofFile1 = f'{main_dir}/Unblinded_{poly1}/higgsCombine_gof_data.GoodnessOfFit.mH120.root'
    # Params for poly 2
    print('######################## POLY 2 ########################\n')
    params2 = twoD.ledger.select(_select_signal, 'NMSSM-XHY-1800-1200', poly2, poly2).alphaParams
    rpfSet2 = params2[params2["name"].str.contains("rpf")]
    rpfSet2 = rpfSet2[~rpfSet2["owner"].str.contains("VR")]
    nRpfs2  = len(rpfSet2.index)
    print(rpfSet2)
    print(f'nParams TF {poly2} : {nRpfs2}')
    _gof_for_FTest(twoD, f'Unblinded_{poly2}', card_or_w=f'initialFitWorkspace_{poly2}.root')
    gofFile2 = f'{main_dir}/Unblinded_{poly2}/higgsCombine_gof_data.GoodnessOfFit.mH120.root'
    # Base F-statistic
    base_fstat = FstatCalc(gofFile1,gofFile2,nRpfs1,nRpfs2,nBins)
    print(f'Base F-statistic calculation: {base_fstat}')
    # Plotting 
    def plot_FTest(base_fstat,nRpfs1,nRpfs2,nBins):
        from ROOT import TF1, TH1F, TLegend, TPaveText, TLatex, TArrow, TCanvas, kBlue, gStyle
        gStyle.SetOptStat(0000)

        if len(base_fstat) == 0: base_fstat = [0.0]

        ftest_p1    = min(nRpfs1,nRpfs2)
        ftest_p2    = max(nRpfs1,nRpfs2)
        ftest_nbins = nBins
        fdist       = TF1("fDist", "[0]*TMath::FDist(x, [1], [2])", 0,max(10,1.3*base_fstat[0]))
        fdist.SetParameter(0,1)
        fdist.SetParameter(1,ftest_p2-ftest_p1)
        fdist.SetParameter(2,ftest_nbins-ftest_p2)

        pval = fdist.Integral(0.0,base_fstat[0] if base_fstat[0] != 0 else 10.0)
        print('P-value: %s'%pval)

        c = TCanvas('c','c',800,600)    
        c.SetLeftMargin(0.12) 
        c.SetBottomMargin(0.12)
        c.SetRightMargin(0.1)
        c.SetTopMargin(0.1)
        ftestHist_nbins = 30
        ftestHist = TH1F("Fhist","",ftestHist_nbins,0,max(10,1.3*base_fstat[0]))
        ftestHist.GetXaxis().SetTitle("F = #frac{-2log(#lambda_{1}/#lambda_{2})/(p_{2}-p_{1})}{-2log#lambda_{2}/(n-p_{2})}")
        ftestHist.GetXaxis().SetTitleSize(0.025)
        ftestHist.GetXaxis().SetTitleOffset(2)
        ftestHist.GetYaxis().SetTitleOffset(0.85)
        
        ftestHist.Draw("pez")
        ftestobs  = TArrow(base_fstat[0],0.25,base_fstat[0],0)
        ftestobs.SetLineColor(kBlue+1)
        ftestobs.SetLineWidth(2)
        fdist.Draw('same')

        ftestobs.Draw()
        tLeg = TLegend(0.6,0.73,0.89,0.89)
        tLeg.SetLineWidth(0)
        tLeg.SetFillStyle(0)
        tLeg.SetTextFont(42)
        tLeg.SetTextSize(0.03)
        tLeg.AddEntry(ftestobs,"observed = %.3f"%base_fstat[0],"l")
        tLeg.AddEntry(fdist,"F-dist, ndf = (%.0f, %.0f) "%(fdist.GetParameter(1),fdist.GetParameter(2)),"l")
        tLeg.Draw("same")

        model_info = TPaveText(0.2,0.6,0.4,0.8,"brNDC")
        model_info.AddText('p1 = '+poly1)
        model_info.AddText('p2 = '+poly2)
        model_info.AddText("p-value = %.2f"%(1-pval))
        model_info.Draw('same')
        
        latex = TLatex()
        latex.SetTextAlign(11)
        latex.SetTextSize(0.06)
        latex.SetTextFont(62)
        latex.SetNDC()
        latex.DrawLatex(0.12,0.91,"CMS")
        latex.SetTextSize(0.05)
        latex.SetTextFont(52)
        latex.DrawLatex(0.65,0.91,"Preliminary")
        latex.SetTextFont(42)
        latex.SetTextFont(52)
        latex.SetTextSize(0.045)
        c.SaveAs(f'{main_dir}/ftest_{poly1}_vs_{poly2}_notoys.png')

    plot_FTest(base_fstat,nRpfs1,nRpfs2,nBins)

def GoF(tf, robustFit=True, rMin=-1, rMax=5, strat=0):
    twoD = TwoDAlphabet(main_dir, '{}/runConfig.json'.format(main_dir), loadPrevious=True)
    twoD.GoodnessOfFit(f'Unblinded_{tf}', ntoys=500, freezeSignal=0, condor=False, card_or_w=f'initialFitWorkspace_{tf}.root', extra=f'--freezeParameters {freeze_VR} --setParameters {mask_VR},{set_VR}')

def GoF_plot(tf):
    plot.plot_gof(main_dir, f'Unblinded_{tf}', condor=False, seed=123456)


def Impacts(tf, unblind=False):
    # twoD = TwoDAlphabet(main_dir, '{}/runConfig.json'.format(main_dir), loadPrevious=True)
    # twoD.Impacts(f'Unblinded_{tf}', rMin=-1, rMax=4, cardOrW=f'initialFitWorkspace.root --snapshotName initialFit', blind=unblind, extra=f'--freezeParameters {freeze_VR} --setParameters {mask_VR},{set_VR} --cminDefaultMinimizerTolerance 5')

    from TwoDAlphabet.twoDalphabet import LoadLedger
    with cd(f'{main_dir}/Unblinded_{tf}'):
        subset = LoadLedger('')
        nuisances = subset.GetAllSystematics()
        nuisances = [n for n in nuisances if 'mcstats' not in n]

        # Initial fit
        initalFit_command = f'(set -x; combineTool.py -M Impacts --snapshotName initialFit -m 125 -n "impacts" -d initialFitWorkspace.root --doInitialFit --rMin -1 --rMax 2 --cminDefaultMinimizerStrategy=0 --cminDefaultMinimizerTolerance 0.1 --X-rtd MINIMIZER_MaxCalls=400000 --setParameters {set_VR},{mask_VR} --freezeParameters {freeze_VR} -v 0) 2>&1 | tee outs/Impacts_init.txt'
        #execute_cmd(initalFit_command)
        # Now all parameters
        for n in nuisances:
            n_cmd = f'(set -x; combine -M MultiDimFit -n _paramFit_impacts_{n} -d initialFitWorkspace.root --snapshotName initialFit --algo impact --redefineSignalPOIs r -P {n} --floatOtherPOIs 1 --saveInactivePOI 1 --setParameters {set_VR},{mask_VR} --freezeParameters {freeze_VR} --floatParameters {float_SR} --setParameterRanges r=-0.5,1 --cminDefaultMinimizerStrategy=0 --robustFit 1 --cminDefaultMinimizerTolerance 10 --X-rtd MINIMIZER_MaxCalls=400000 -v 0 -m 125) 2>&1 | tee outs/Impacts_{n}.txt'
            #execute_cmd(n_cmd)
        # Now collect
        c_cmd = f'(set -x; combineTool.py -M Impacts --snapshotName initialFit -m 125 -n "impacts" -d initialFitWorkspace.root --named {",".join(nuisances)} --setParameterRanges r=-0.5,20 -v 0 -o impacts{"_blind" if not unblind else ""}.json) 2>&1 | tee outs/Impacts_collect.txt'
        execute_cmd(c_cmd)
        # Plot
        execute_cmd(f'plotImpacts.py -i impacts{"_blind" if not unblind else ""}.json -o impacts{"_blind" if not unblind else ""} {"--blind" if not unblind else ""}')

if __name__ == "__main__":

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--tf', type=str, dest='tf',
                        action='store', required=True,
                        help='TF parameterization choice for the SR')
    parser.add_argument('--condor', dest='condor',
                        action='store_true',
                        help='If passed as argument, use Condor for methods')
    parser.add_argument('--makeCard', dest='makeCard',
                        action='store_true', 
                        help='If passed as argument, create Combine card for given TF')
    parser.add_argument('--fit', dest='fit',
                        action='store_true',
                        help='If passed as argument, fit with the given TFs')
    parser.add_argument('--FTest', dest='ftest',
                        action='store_true',
                        help='Run F-test using the two polynominals provided via --poly1 and --poly2 args')
    parser.add_argument('--poly1', dest='poly1',
                        action='store', default='0x0',
                        help='TF polynomial 1 used for F-test. Should be subset of poly2 (lower order than poly2)')
    parser.add_argument('--poly2', dest='poly2',
                        action='store', default='0x1',
                        help='TF polynomial 2 used for F-test. Should be higher-order than poly1')
    parser.add_argument('--gof', dest='gof',
                        action='store_true',
                        help='If passed as argument, run GoF test for the fit with the given TFs')
    parser.add_argument('--gofplot', dest='gofplot',
                        action='store_true',
                        help='If passed as argument, run GoF test for the fit with the given TFs')
    parser.add_argument('--plot', dest='plot',
                        action='store_true',
                        help='If passed as argument, plot fit result for the given TF')
    parser.add_argument('--impacts', dest='impacts',
                        action='store_true',
                        help='If passed as argument, run impacts for the fit with the given TFs')
    parser.add_argument('--limit', dest='limit',
                        action='store_true',
                        help='If passed as argumnet, run the limit for the fit with the given TFs')
    parser.add_argument('--analyzeNLL', dest='analyzeNLL',
                        action='store_true',
                        help='Analyze NLL as function of all nuisances')
    # Fit options
    parser.add_argument('--strat', dest='strat',
                        action='store', default='0',
                        help='Default minimizer strategy')
    parser.add_argument('--tol', dest='tol',
                        action='store', default='0.1',
                        help='Default minimizer tolerance')
    parser.add_argument('--robustFit', dest='robustFit',
                        action='store_true',
                        help='If passed as argument, uses robustFit algo')
    parser.add_argument('--robustHesse', dest='robustHesse',
                        action='store_true',
                        help='If passed as argument, uses robustHesse algo')
    parser.add_argument('--rMin', dest='rMin',
                        action='store', default='-1',
                        help='Minimum allowed signal strength')
    parser.add_argument('--rMax', dest='rMax',
                        action='store', default='10',
                        help='Maximium allowed signal strength')
    parser.add_argument('-v', dest='verbosity',
                        action='store', default='2',
                        help='Combine verbosity')
    parser.add_argument('--unblind', dest='unblind',
                        action='store_true',
                        help='unblind impact plot')

    args = parser.parse_args()

    if args.makeCard:
        make_card(args.tf)
    
    if args.fit:
        FitDiagnostics(tf=args.tf, strat=args.strat, tol=args.tol, robustFit=args.robustFit, rMin=args.rMin, rMax=args.rMax, verbosity=args.verbosity)

    if args.plot:
        PlotFit(args.tf)

    if args.ftest:
        FTest(args.poly1, args.poly2)

    if args.gof:
        GoF(args.tf, robustFit=args.robustFit, rMin=args.rMin, rMax=args.rMax, strat=args.strat)

    if args.impacts:
        Impacts(args.tf, args.unblind)

    if args.gofplot:
        GoF_plot(args.tf)
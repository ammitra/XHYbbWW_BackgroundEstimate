from time import time

from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from TwoDAlphabet.helpers import make_env_tarball, cd, execute_cmd
from TwoDAlphabet.ftest import FstatCalc
import os
import numpy as np
import subprocess

def _get_other_region_names(pass_reg_name):
    return pass_reg_name, pass_reg_name.replace('VR_fail','SR_pass')

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

def _generate_constraints(nparams):
    out = {}
    for i in range(nparams):
        if i == 0:
            out[i] = {"MIN":-500,"MAX":500}
        else:
            out[i] = {"MIN":-500,"MAX":500}
    return out

_rpf_options = {
    '0x0': {
        'form': '(@0)',
        'constraints': _generate_constraints(1)
    },
    '1x0': {
        'form': '(@0+@1*x)',
        'constraints': _generate_constraints(2)
    },
    '0x1': {
        'form': '(@0+@1*y)',
        'constraints': _generate_constraints(2)
    },
    '1x1': {
        'form': '(@0+@1*x)*(@2+@3*y)',
        'constraints': _generate_constraints(4)
    },
    '2x1': {
        'form': '(@0+@1*x+@2*x**2)*(@3+@4*y)',
        'constraints': _generate_constraints(5)
    },
    '2x2': {
        'form': '(@0+@1*x+@2*x**2)*(@3+@4*y*@5*y**2)',
        'constraints': _generate_constraints(6)
    },
    '3x2': {
        'form': '(@0+@1*x+@2*x**2+@3*x**3)*(@4+@5*y)',
        'constraints': _generate_constraints(6)
    }
}

def test_make(SRorVR='',fr={}, json=''):
    twoD = TwoDAlphabet('{}fits'.format(SRorVR),json,loadPrevious=False,findreplace=fr)
    qcd_hists = twoD.InitQCDHists()

    binning, _ = twoD.GetBinningFor('VR_fail')

    # Set up QCD estimate in VR_fail
    vr_fail_name = 'Background_VR_fail'
    qcd_vr_f     = BinnedDistribution(vr_fail_name, qcd_hists['VR_fail'], binning, constant=False)
    twoD.AddAlphaObj('Background_VR_fail', 'VR_fail', qcd_vr_f, title='QCD')

    # Set up QCD estimate in SR_fail
    sr_fail_name = 'Background_SR_fail'
    qcd_sr_f     = BinnedDistribution(sr_fail_name, qcd_hists['SR_fail'], binning, constant=False)
    twoD.AddAlphaObj('Background_SR_fail', 'SR_fail', qcd_sr_f, title='QCD')

    # Try all TFs for the VR and SR
    for opt_name, opt in _rpf_options.items():
        # We need to ensure that the QCD transfer function name is the same for VR and SR
        qcd_rpf = ParametricFunction(
            f'Background_rpf_{opt_name}', binning, opt['form'],
            constraints = opt['constraints']
        )
        # QCD estimate in VR and SR pass
        qcd_vr_p = qcd_vr_f.Multiply(vr_fail_name.replace('fail','pass')+'_'+opt_name, qcd_rpf)
        qcd_sr_p = qcd_sr_f.Multiply(sr_fail_name.replace('fail','pass')+'_'+opt_name, qcd_rpf)
        twoD.AddAlphaObj(f'Background_VR_pass_{opt_name}', 'VR_pass', qcd_vr_p, title='QCD')
        twoD.AddAlphaObj(f'Background_SR_pass_{opt_name}', 'SR_pass', qcd_sr_p, title='QCD')

    twoD.Save()


def make_card(SRorVR='', signal='', SRtf='', VRtf=''):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), SRtf, VRtf)
    twoD.MakeCard(subset, 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal, SRtf, VRtf))

def make_card_unblinded(SRorVR='', signal='', SRtf='', VRtf=''):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), SRtf, VRtf)
    twoD.MakeCard(subset, f'Unblinded_{SRtf}')

def test_fit(SRorVR='', signal='', SRtf='', VRtf='', defMinStrat=0, extra='--robustHesse 1', rMin=-1, rMax=10, setParams={}, verbosity=2):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), SRtf, VRtf)
    twoD.MakeCard(subset, 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal, SRtf, VRtf))
    twoD.MLfit('NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal,SRtf,VRtf),rMin=rMin,rMax=rMax,setParams=setParams,verbosity=verbosity,defMinStrat=defMinStrat,extra=extra)

def test_plot(SRorVR='', signal='', SRtf='', VRtf=''):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), SRtf, VRtf)
    # customize the plots to include region definitions
    subtitles = {
        "VR_fail": r"Validation region;$T_{Xbb} < 0.98$",
        "VR_pass": r"Validation region;$T_{Xbb} \geq 0.98$",
        "SR_fail": r"Signal region;$T_{Xbb} < 0.98$",
        "SR_pass": r"Signal region;$T_{Xbb} \geq 0.98$"
    }
    regions = [['VR']]
    twoD.StdPlots('NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal,SRtf,VRtf), subset, subtitles=subtitles, regionsToGroup=regions)

def _gof_for_FTest(twoD, subtag, card_or_w='card.txt'):

    run_dir = twoD.tag+'/'+subtag
    
    with cd(run_dir):
        gof_data_cmd = [
            'combine -M GoodnessOfFit',
            '-d '+card_or_w,
            '--algo=saturated',
            '-n _gof_data'
        ]

        gof_data_cmd = ' '.join(gof_data_cmd)
        execute_cmd(gof_data_cmd)

def test_FTest(poly1, poly2, SRorVR='', signal=''):
    '''
    Perform an F-test using existing working areas
    '''
    working_area = '{}fits'.format(SRorVR)
    
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    binning = twoD.binnings['default']
    nBins = (len(binning.xbinList)-1)*(len(binning.ybinList)-1)
    
    # Get number of RPF params and run GoF for poly1
    params1 = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), poly1, poly1).alphaParams
    rpfSet1 = params1[params1["name"].str.contains("rpf")]
    nRpfs1  = len(rpfSet1.index)
    _gof_for_FTest(twoD, 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal, poly1, poly1), card_or_w='initialFitWorkspace.root')
    gofFile1 = working_area+'/NMSSM-XHY-{}-SR{}-VR{}_area/higgsCombine_gof_data.GoodnessOfFit.mH120.root'.format(signal,poly1,poly1)

    # Get number of RPF params and run GoF for poly2
    params2 = twoD.ledger.select(_select_signal, 'NMSSM-XHY-{}'.format(signal), poly2, poly2).alphaParams
    rpfSet2 = params2[params2["name"].str.contains("rpf")]
    nRpfs2  = len(rpfSet2.index)
    _gof_for_FTest(twoD, 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal,poly2,poly2), card_or_w='initialFitWorkspace.root')
    gofFile2 = working_area+'/NMSSM-XHY-{}-SR{}-VR{}_area/higgsCombine_gof_data.GoodnessOfFit.mH120.root'.format(signal,poly2,poly2)

    base_fstat = FstatCalc(gofFile1,gofFile2,nRpfs1,nRpfs2,nBins)
    print(base_fstat)

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

        pval = fdist.Integral(0.0,base_fstat[0])
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
        c.SaveAs(working_area+'/ftest_{0}_vs_{1}_notoys.png'.format(poly1,poly2))

    plot_FTest(base_fstat,nRpfs1,nRpfs2,nBins)


def test_GoF(SRorVR, signal, SRtf='', VRtf='', condor=True, extra='', appendName=''):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    signame = 'NMSSM-XHY-'+signal
    if not os.path.exists(twoD.tag+'/'+signame+'-SR{}-VR{}_area/card.txt'.format(SRtf,VTtf)):
        subset = twoD.ledger.select(_select_signal, signame, SRtf, VRtf)
        twoD.MakeCard(subset, 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal, SRtf, VRtf))
    if condor == False:
        twoD.GoodnessOfFit(
            signame+'-SR{}-VR{}_area'.format(SRtf,VRtf), ntoys=500, freezeSignal=0,
            condor=False, card_or_w='initialFitWorkspace.root', extra=extra, appendName=appendName
        )
    else:
        twoD.GoodnessOfFit(
            signame+'-SR{}-VR{}_area'.format(SRtf,VRtf), ntoys=500, freezeSignal=0,
            condor=True, njobs=50, card_or_w='initialFitWorkspace.root', 
            extra=extra, appendName=appendName,
            eosRootfiles='root://cmseos.fnal.gov//store/user/ammitra/XHY_2D_env.tgz'
        )

def test_GoF_plot(SRorVR, signal, SRtf='', VRtf='', condor=True, appendName=''):
    '''Plot the GoF for a given fit (condor=True indicates that condor jobs need to be unpacked)'''
    signame = 'NMSSM-XHY-'+signal
    plot.plot_gof(f'{SRorVR}fits','{}-SR{}-VR{}_area'.format(signame,SRtf,VRtf), seed=42, condor=condor, appendName=appendName)

def load_RPF(twoD, signal='1800-125', SRtf='', VRtf=''):
    params_to_set = twoD.GetParamsOnMatch('rpf.*', 'NMSSM-XHY-{}-SR{}-VR{}_area'.format(signal,SRtf,VRtf), 'b')
    return {k:v['val'] for k,v in params_to_set.items()}

def test_SigInj(SRorVR, r, signal='1800-125', tf='', extra='', condor=True):
    '''Perform a signal injection test'''
    twoD = TwoDAlphabet('{}fits'.format(SRorVR), '{}fits/runConfig.json'.format(SRorVR), loadPrevious=True)
    params = load_RPF(twoD,signal,tf)
    twoD.SignalInjection(
        'NMSSM-XHY-{}-{}_area'.format(signal,tf),
        injectAmount = r,       # amount of signal to inject (r=0 <- bias test)
        ntoys = 500,
        njobs = 50,
        blindData = False,      # working with toy data, no need to blind
        setParams = params,     # give the toys the same RPF params
        verbosity = 0,
        extra = extra,
        condor = condor)

def test_SigInj_plot(SRorVR, r, signal='1800-125', tf='', condor=False):
    plot.plot_signalInjection('{}fits'.format(SRorVR),'NMSSM-XHY-{}-{}_area'.format(signal,tf), injectedAmount=r, condor=condor)

def test_Impacts(SRorVR, signal='1800-125', tf=''):
    twoD = TwoDAlphabet('{}fits'.format(SRorVR), '{}fits/runConfig.json'.format(SRorVR), loadPrevious=True)
    twoD.Impacts('NMSSM-XHY-{}-{}_area'.format(signal,tf), rMin=-1, rMax=4, extra='')

def test_limits(SRorVR, signal, tf):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    twoD.Limit(
        subtag='{}-{}_area'.format(signal, tf),
        blindData=False,        # BE SURE TO CHANGE THIS IF YOU NEED TO BLIND YOUR DATA
        verbosity=2,
        condor=False
    )

def test_analyze(SRorVR, signal, tf):
    working_area = '{}fits'.format(SRorVR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    twoD.AnalyzeNLL(subtag='NMSSM-XHY-{}-{}_area'.format(signal, tf))

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-w', type=str, dest='workspace',
                        action='store', default='VR',
                        help='workspace name')
    parser.add_argument('-s', type=str, dest='sigmass',
                        action='store', default='1800-125',
                        help='mass of X and Y cands')
    parser.add_argument('--json', type=str, dest='json',
                        action='store', default='VR.json',
                        help='JSON config file to use for workspace creation')
    parser.add_argument('--SRtf', type=str, dest='SRtf',
                        action='store', required=True,
                        help='TF parameterization choice for the SR')
    parser.add_argument('--VRtf', type=str, dest='VRtf',
                        action='store', required=True,
                        help='TF parameterization choice for the VR')
    parser.add_argument('--condor', dest='condor',
                        action='store_true',
                        help='If passed as argument, use Condor for methods')
    parser.add_argument('--make', dest='make',
                        action='store_true', 
                        help='If passed as argument, create 2DAlphabet workspace')
    parser.add_argument('--makeCard', dest='makeCard',
                        action='store_true', 
                        help='If passed as argument, create Combine card for given SRtf, VRtf combo')
    parser.add_argument('--makeCardUnblinded', dest='makeCardUnblinded',
                        action='store_true', 
                        help='If passed as argument, create Combine card for SRtf, unblinded')
    parser.add_argument('--fit', dest='fit',
                        action='store_true',
                        help='If passed as argument, fit with the given TFs')
    parser.add_argument('--plot', dest='plot',
                        action='store_true',
                        help='If passed as argument, plot the result of the fit with the given TFs')
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
    parser.add_argument('--rinj', type=float, dest='rinj',
                        action='store', default='0.0',
                        help='Value of signal strength to inject')
    parser.add_argument('--inject', dest='inject',
                        action='store_true',
                        help='If passed as argument, run signal injection test for the fit with the given TFs')
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

    args = parser.parse_args()

    if args.make:
        MX = args.sigmass.split('-')[0]
        MY = args.sigmass.split('-')[-1]
        fr = {'NMSSM-XHY-XMASS-YMASS':f'NMSSM-XHY-{MX}-{MY}'}
        test_make(args.workspace, fr=fr, json=args.json)
    if args.makeCard:
        make_card(SRorVR=args.workspace, signal=args.sigmass, SRtf=args.SRtf, VRtf=args.VRtf)
    if args.makeCardUnblinded:
        make_card_unblinded(SRorVR=args.workspace, signal=args.sigmass, SRtf=args.SRtf, VRtf=args.VRtf)
    if args.fit:
        if (args.robustFit) and (args.robustHesse):
            raise ValueError('Cannot use both robustFit and robustHesse algorithms simultaneously')
        elif (args.robustFit) or (args.robustHesse):
            if args.robustFit:
                algo = f'--robustFit 1'
            else:
                algo = f'--robustHesse 1'
        else:
            algo = ''
        # Channel masks to fully mask the SR and only fit the VR
        masks = {}
        for region in ['SR_fail','SR_pass','VR_fail','VR_pass']:
            for channel in ['LOW','SIG','HIGH']:
                if ('SR' in region):
                    masks[f'mask_{region}_{channel}'] = '1'
                else:
                    masks[f'mask_{region}_{channel}'] = '0'
        masks['rgx{Background_SR_.*}'] = '1'
        freeze_params = 'var{Background_SR.*}'

        test_fit(
            args.workspace,
            args.sigmass,
            SRtf=args.SRtf,
            VRtf=args.VRtf,
            defMinStrat=int(args.strat),
            extra=f'{algo} --cminDefaultMinimizerTolerance {args.tol} --freezeParameters {freeze_params} --X-rtd MINIMIZER_MaxCalls=400000',
            rMin=args.rMin,
            rMax=args.rMax,
            setParams=masks,
            verbosity=args.verbosity
        )

    if args.plot:
        test_plot(args.workspace, args.sigmass, SRtf=args.SRtf, VRtf=args.VRtf)
    if args.ftest:
        test_FTest(args.poly1, args.poly2, args.workspace, args.sigmass)
    if args.gof:
        #subprocess.check_output(f'source scripts/run_gof.sh {args.sigmass} {args.SRtf} {args.VRtf}',shell=True)
        test_GoF_plot(args.workspace, args.sigmass, SRtf=args.SRtf, VRtf=args.VRtf, condor=False, appendName='')
    if args.inject:
        test_SigInj(args.workspace, args.rinj, args.sigmass, args.tf, condor=args.condor)
        #test_SigInj_plot(args.workspace, args.rinj, args.sigmass, args.tf, condor=args.condor)
    if args.impacts:
        test_Impacts(args.workspace, args.sigmass, args.tf)
    if args.limit:
        subprocess.check_output(f'source scripts/run_limit.sh {args.sigmass} {args.SRtf} {args.VRtf}',shell=True)
    if args.analyzeNLL:
        test_analyze(args.workspace, args.sigmass, args.tf)


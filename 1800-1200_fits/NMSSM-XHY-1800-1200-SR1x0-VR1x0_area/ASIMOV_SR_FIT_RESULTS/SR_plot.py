import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from TwoDAlphabet.helpers import make_env_tarball, cd, execute_cmd
from TwoDAlphabet.ftest import FstatCalc
import os
import numpy as np
import subprocess

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

def SR_plot():
    working_area = '/uscms/home/ammitra/nobackup/2DAlphabet/fitting/CMSSW_14_1_0_pre4/src/XHYbbWW/1800-1200_fits'
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'NMSSM-XHY-1800-1200', '1x0', '1x0')
    # customize the plots to include region definitions
    subtitles = {
        "VR_fail": r"Validation region;$T_{Xbb} < 0.98$",
        "VR_pass": r"Validation region;$T_{Xbb} \geq 0.98$",
        "SR_fail": r"Signal region (Asimov);$T_{Xbb} < 0.98$",
        "SR_pass": r"Signal region (Asimov);$T_{Xbb} \geq 0.98$"
    }
    regions = [['SR']]

    plot.gen_projections(ledger=subset, twoD=twoD, fittag='b', lumiText=r'138 $fb^{-1}$ (13 TeV)', extraText='Preliminary', subtitles=subtitles, units='GeV', regionsToGroup=regions)

SR_plot()

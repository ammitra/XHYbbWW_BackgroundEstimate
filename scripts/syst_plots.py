import ROOT
from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
import subprocess 

def make_systematic_plots(sig, do=''):
    working_area = '{}_fits'.format(sig)
    subprocess.check_output(f'mkdir -p {working_area}/UncertPlots',shell=True)    
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    plot.make_systematic_plots(twoD, do)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='sigmass',
                        action='store', default='1800-125',
                        help='mass of X and Y cands')
    parser.add_argument('--do', type=str, dest='do',
                        action='store', default='',
                        help='systematic name (or portion of it) to plot. All others will be skipped')
    args = parser.parse_args()

    make_systematic_plots(args.sigmass, args.do)

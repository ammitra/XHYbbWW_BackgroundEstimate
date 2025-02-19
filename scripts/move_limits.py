'''
Script to gather all limits files from Condor and send them to their respective workspaces.
The script "condor/submit_limits.py" sends the output AsymptoticLimits files to the main directory, 
this script just sends them to their proper location. 
'''
import subprocess, glob
from TwoDAlphabet.helpers import execute_cmd

def get(args):
    # Output files are in the format higgsCombine.AsymptoticLimits.mH125.$signame.$seed.root
    g = glob.glob('higgsCombine.AsymptoticLimits.*')

    for f in g:
        signame = f.split('.')[3]
        print(f'Detected AsymptoticLimits file for signal {signame} - relocating...')
        if args.unblinded:
            toDir = f'{signame}_fits/Unblinded_{args.tf}/'
        else:
            toDir = f'{signame}_fits/NMSSM-XHY-{signame}-SR{args.tf}-VR{args.tf}_area/'
        execute_cmd(f'mv {f} {toDir}')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # GET THE APPROPRIATE INPUT FILES
    parser.add_argument("--tf", default="1x0", help="QCD transfer function parameterization", type=str)
    parser.add_argument("--unblinded", action='store_true', dest='unblinded')
    args = parser.parse_args()
    get(args)
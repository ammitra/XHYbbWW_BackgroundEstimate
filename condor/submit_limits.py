'''
NOTE: This script does not require that the RooWorkspace exists, only that the combined card exists locally
'''
import os 
from pathlib import Path
import argparse
from string import Template

def setup():
    t2_local_prefix = "/eos/uscms/"
    t2_prefix = "root://cmseos.fnal.gov"
    
    proxy = '/uscms/home/ammitra/x509up_u56971'

    username = os.environ["USER"]
    submitdir = Path(__file__).resolve().parent

    return t2_local_prefix, t2_prefix, proxy, username, submitdir

def write_template(templ_file: str, out_file: Path, templ_args: dict, safe: bool = False):
    """Write to ``out_file`` based on template from ``templ_file`` using ``templ_args``"""

    with Path(templ_file).open() as f:
        templ = Template(f.read())

    with Path(out_file).open("w") as f:
        if not safe:
            f.write(templ.substitute(templ_args))
        else:
            f.write(templ.safe_substitute(templ_args))

def main(args):
    t2_local_prefix, t2_prefix, proxy, username, submitdir = setup()
    prefix = f"limits_seed_{args.seed}"
    local_dir = Path(f"condor/limits/{args.sig}/{prefix}")

    # make local directory for output
    logdir = local_dir / "logs"
    logdir.mkdir(parents=True, exist_ok=True)

    jdl_templ = f"{submitdir}/submit_limits.templ.jdl"
    sh_templ = f"{submitdir}/submit_limits.templ.sh"

    # get the location of the cards and base.root
    cards_dir     = Path(f'{args.sig}_fits/NMSSM-XHY-{args.sig}-SR{args.tf}-VR{args.tf}_area')
    base_root_dir = Path(f'{args.sig}_fits')

    local_jdl = Path(f'{local_dir}/{prefix}.jdl')
    local_log = Path(f'{local_dir}/{prefix}.log')

    # Arguments for jdl 
    jdl_args = {
        "dir": local_dir,
        "prefix": prefix,
        "cards_dir": cards_dir,
        "base_root_dir": base_root_dir,
        "signame": args.sig,
        "seed": args.seed
    }
    write_template(jdl_templ, local_jdl, jdl_args)

    # Arguments for condor shell script
    localsh = f"{local_dir}/{prefix}.sh"
    sh_args = {
        "seed": args.seed,
        "tol": args.tol,
        "strat": args.strat,
        "cards_dir": cards_dir,
        "sig": args.sig,
        "tf": args.tf, 
        "rMin": args.rMin,
        "rMax": args.rMax
    }
    write_template(sh_templ, localsh, sh_args)

    os.system(f"chmod u+x {localsh}")

    if local_log.exists():
        local_log.unlink()

    os.system(f"condor_submit {local_jdl}")
    print("To submit ", local_jdl)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # GET THE APPROPRIATE INPUT FILES
    parser.add_argument("--sig", help="signal name", type=str, required=True)
    parser.add_argument("--tf", default="1x0", help="QCD transfer function parameterization", type=str)
    # FIT ARGUMENTS 
    parser.add_argument("--seed", default=42, help="# condor jobs", type=int)
    parser.add_argument("--tol", default=0.1, help="minimizer tolerance", type=float)
    parser.add_argument("--strat", default=2, help='minimizer strategy', type=int)
    parser.add_argument("--rMin", default='-1', help='rMin in fit', type=str)
    parser.add_argument("--rMax", default='2', help='rMax in fit', type=str)
    args = parser.parse_args()

    # check if the required input files have been produced already. This script only needs a combined card
    for fname in ['card.txt']:
        cards_dir = Path(f'{args.sig}_fits/NMSSM-XHY-{args.sig}-SR{args.tf}-VR{args.tf}_area')
        if not os.path.isfile(f'{cards_dir}/{fname}'):
            raise FileNotFoundError(f'ERROR: File ${cards_dir}/{fname} required for this script not found. Generate it first with the command:\n\t./scripts/run_blinded.sh --sig {args.sig} --tf {args.tf} -w')

    main(args)
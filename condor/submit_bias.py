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
    prefix = f"bias_{args.bias}_seed_{args.seed}"
    local_dir = Path(f"condor/bias/{args.sig}/{prefix}")

    # make local directory for output
    logdir = local_dir / "logs"
    logdir.mkdir(parents=True, exist_ok=True)

    jdl_templ = f"{submitdir}/submit_bias.templ.jdl"
    sh_templ = f"{submitdir}/submit_bias.templ.sh"

    # get the location of the cards
    cards_dir = Path(f'{args.sig}_fits/NMSSM-XHY-{args.sig}-SR{args.tf}-VR{args.tf}_area')

    for j in range(args.num_jobs):
        local_jdl = Path(f"{local_dir}/{prefix}_{j}.jdl")
        local_log = Path(f"{local_dir}/{prefix}_{j}.log")

        # Arguments for the jdl file
        seed = args.seed + j * args.toys_per_job
        jdl_args = {
            "dir": local_dir,
            "cards_dir": cards_dir,
            "prefix": prefix,
            "jobid": j,
            "proxy": proxy,
            "bias": args.bias,
            "seed": seed,
        }
        write_template(jdl_templ, local_jdl, jdl_args)

        # Arguments that get passed to the condor shell script, which in turn get passed to run_blinded.sh
        localsh = f"{local_dir}/{prefix}_{j}.sh"
        sh_args = {
            "seed": seed,
            "num_toys": args.toys_per_job,
            "bias": args.bias,
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
    # CONDOR ARGS
    parser.add_argument("--toys-per-job", default=50, help="# toys per condor job", type=int)
    parser.add_argument("--num-jobs", default=10, help="# condor jobs", type=int)
    # FIT ARGUMENTS 
    parser.add_argument("--bias", help="expected signal strength to test", type=float, required=True)
    parser.add_argument("--seed", default=42, help="# condor jobs", type=int)
    parser.add_argument("--tol", default=0.1, help="minimizer tolerance", type=float)
    parser.add_argument("--strat", default=2, help='minimizer strategy', type=int)
    parser.add_argument("--rMin", default='-15', help='rMin in fit', type=str)
    parser.add_argument("--rMax", default='15', help='rMax in fit', type=str)
    args = parser.parse_args()

    # check if the required input files have been produced already 
    for fname in ['initialFitWorkspace.root','higgsCombineSnapshot.MultiDimFit.mH125.root']:
        cards_dir = Path(f'{args.sig}_fits/NMSSM-XHY-{args.sig}-SR{args.tf}-VR{args.tf}_area')
        if not os.path.isfile(f'{cards_dir}/{fname}'):
            raise FileNotFoundError(f'ERROR: File ${cards_dir}/{fname} required for bias test not found. Generate it first with the command:\n\t./scripts/run_blinded.sh --sig {args.sig} --tf {args.tf} --seed {args.seed} --tol {args.tol} --strat {args.strat} --rmin {args.rMin} --rmax {args.rMax} --verbosity 2 -wb')

    main(args)

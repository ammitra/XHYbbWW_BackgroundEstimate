'''
Submit deltaNLL scans as a function of each parameter of interest
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

params = ["Background_rpf_1x0_par0","Background_rpf_1x0_par1","CMS_bbWW_PNetHbb_mistag","CMS_bbWW_PNetHbb_tag","CMS_bbWW_PNetWqq_mistag","CMS_bbWW_PNetWqq_tag","CMS_l1_ecal_prefiring_2016","CMS_l1_ecal_prefiring_2017","CMS_pileup_2016","CMS_pileup_2017","CMS_pileup_2018","CMS_res_j_2016","CMS_res_j_2017","CMS_res_j_2018","CMS_res_jm_2016","CMS_res_jm_2017","CMS_res_jm_2018","CMS_scale_j_2016","CMS_scale_j_2017","CMS_scale_j_2018","CMS_scale_jm_2016","CMS_scale_jm_2017","CMS_scale_jm_2018","QCDscale_V","QCDscale_ttbar","lumi_13TeV_2016","lumi_13TeV_2017","lumi_13TeV_2018","lumi_correlated","ps_fsr","ps_isr"]

def main(plot=False):
    for param in params:
        t2_local_prefix, t2_prefix, proxy, username, submitdir = setup()
        prefix = f"dNLL_{param}"
        local_dir = Path(f"./condor/{prefix}")

        # make local directory for output
        logdir = local_dir / "logs"
        logdir.mkdir(parents=True, exist_ok=True)

        jdl_templ = f"./submit_dNLL.templ.jdl"
        sh_templ  = f"./submit_dNLL.templ.sh"

        local_jdl = Path(f"{local_dir}/{prefix}.jdl")
        local_log = Path(f"{local_dir}/{prefix}.log")

        # Arguments for the jdl file
        jdl_args = {
            "dir": local_dir,
            "prefix": prefix, 
            "param": param
        } 
        write_template(jdl_templ, local_jdl, jdl_args, safe=True)

        # custom args for some params
        if param == 'Background_rpf_1x0_par1':
            pMin = 0
            pMax = 0.3
            yMax = 8
        elif param == 'Background_rpf_1x0_par0':
            pMin = 0.025
            pMax = 0.035
            yMax = 2
        else: 
            pMin = -3
            pMax = 3
            yMax = 8

        # Arguments for shell script
        localsh = f"{local_dir}/{prefix}.sh"
        sh_args = {
            "param": param,
            "pMin": pMin,
            "pMax": pMax,
            "yMax": yMax
        }
        write_template(sh_templ, localsh, sh_args, safe=True)

        os.system(f"chmod u+x {localsh}")

        if local_log.exists():
            local_log.unlink()

        if plot:
            print(f'Plotting {param}')
            os.system(f'plot1DScan.py "higgsCombine.{param}.MultiDimFit.mH120.root" -o "dNLL_{param}" --POI {param} --y-max {yMax}')
        else:
            os.system(f"condor_submit {local_jdl}")
            print("To submit ", local_jdl)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", help="plot 1D scan of NLL as function of all parameters", action='store_true')
    args = parser.parse_args()

    main(plot=args.plot)

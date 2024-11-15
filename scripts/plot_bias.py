'''
Adapted from Raghav Kansal's code:
https://github.com/rkansal47/HHbbVV/blob/cd41daa657e1581b789b145f7a93e6dc81cb4ab6/src/HHbbVV/combine/binder/BiasTest.ipynb
'''
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import mplhep as hep
import numpy as np
import uproot
from scipy import stats

def plot_bias(inDir, bias):
    # Assume this will always have been run on Condor, thus multiple files
    files = f'{inDir}/higgsCombinebias{bias}*.root'
    f = uproot.concatenate(files)

    r = np.array(f.limit)[::4]
    neg_lim = np.array(f.limit)[1::4]
    pos_lim = np.array(f.limit)[2::4]
    r_negerr = r - neg_lim
    r_poserr = pos_lim - r
    reldiff = r - bias
    reldiff[reldiff < 0] = (reldiff / r_poserr)[reldiff < 0]
    reldiff[reldiff > 0] = (reldiff / r_negerr)[reldiff > 0]

    r_dict = {
        "r": r,
        "reldiff": reldiff,
        "neg_lim": neg_lim,
        "pos_lim": pos_lim,
    }

    # we use rmin and rmax bounds of +/- 15
    r_bounds = [-15, 15]

    # checking in how many fits the ±r values are at the parameter boundary i.e. they are unreliable
    num_toys = len(r_dict["r"])

    print(
        f"For r = {bias}, # of successful fits: = {num_toys}, {np.sum(r_dict['neg_lim'] == r_bounds[0]) / num_toys * 100:.0f}% of these with r- = {r_bounds[0]}, {np.sum(r_dict['pos_lim'] == r_bounds[1]) / num_toys * 100 :.0f}% with r+ = {r_bounds[1]}"
    )

    # checking in how many fits the ±r values are at the parameter boundary AND that side is the one we care about
    r_lims_bounds = (
        (r_dict["reldiff"] < 0)
        * (np.isclose(r_dict["pos_lim"], r_bounds[1]))
    ) + (
        (r_dict["reldiff"] > 0)
        * (np.isclose(r_dict["neg_lim"], r_bounds[0]))
    )

    r_lims_wrong = r_dict["pos_lim"] == r_dict["neg_lim"]

    tot_pfail = np.sum(r_lims_bounds + r_lims_wrong)

    print(
        f"For r = {bias}, # of successful fits: = {num_toys}, {tot_pfail / num_toys * 100:.0f}% of these with r-lim at boundary"
    )

    # Now plot everything
    xrange = 3
    bins = 21
    x = np.linspace(-xrange, xrange, 101)

    fig, ax = plt.subplots(figsize=(8,6), dpi=150)

    r_lims_bounds = (
        (r_dict["reldiff"] < 0)
        * (np.isclose(r_dict["pos_lim"], r_bounds[1]))
    ) + (
        (r_dict["reldiff"] > 0)
        * (np.isclose(r_dict["neg_lim"], r_bounds[0]))
    )

    r_lims_same = r_dict["pos_lim"] == r_dict["neg_lim"]

    fit_fail = r_lims_bounds + r_lims_same

    r = r_dict["r"][~fit_fail]
    reldiff = r_dict["reldiff"][~fit_fail]
    reldiff = reldiff[(reldiff > -xrange) * (reldiff < xrange)]

    mu, sigma = np.mean(reldiff), np.std(reldiff)

    ax.hist(reldiff, np.linspace(-xrange, xrange, bins + 1), histtype="step")
    ax.plot(
        x,
        # scale by bin width
        stats.norm.pdf(x, loc=mu, scale=sigma) * len(r) * (2 * xrange / bins),
        label=rf"$\mu = {mu:.2f}, \sigma = {sigma:.2f}$",
    )
    ax.set_xlabel(rf"$\frac{{\hat{{r}} - {bias}}}{{\Delta \hat r}}$")
    ax.set_ylabel("Number of toys")
    ax.set_title(f"r = {bias}")
    ax.legend()

    hep.cms.label(
        "Preliminary",
        ax=ax,
        data=True,
        lumi=138,
        year=None,
    )

    print(f"Saving figure {inDir}/bias_{str(bias).replace('.','p')}.pdf")
    plt.savefig(f"{inDir}/bias_{str(bias).replace('.','p')}.pdf", bbox_inches="tight")


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--tf', type=str, dest='tf',
                        action='store', required=True,
                        help='transfer function parameterization')
    parser.add_argument('--sig', type=str, dest='sig',
                        action='store', required=True,
                        help='signal mass')
    parser.add_argument('--bias', type=float, dest='bias',
                        action='store', required=True,
                        help='injected signal strength (include decimal point)')

    args = parser.parse_args()

    indir = f'{args.sig}_fits/NMSSM-XHY-{args.sig}-SR{args.tf}-VR{args.tf}_area'
    plot_bias(indir, args.bias)
#!/bin/bash
####################################################################################################
# Script for fits
#
# 1) Makes a workspace and creates the combined VR+SR card (--workspace / -w)
# 2) Background-only fit (--bfit / -b)
# 3) Expected asymptotic limits (--limits / -l)
# 4) Expected significance (--significance / -s)
# 5) Fit diagnostics (--dfit / -d)
# 6) GoF on data (--gofdata / -g)
# 7) GoF on toys (--goftoys / -t),
# 8) Impacts: initial fit (--impactsi / -i), per-nuisance fits (--impactsf $nuisance), collect (--impactsc $nuisances)
# 9) Bias test: run a bias test on toys (using post-fit nuisances) with expected signal strength
#    given by --bias X.
#
# Specify seed with --seed (default 42) and number of toys with --numtoys (default 100)
#
# Usage ./scripts/run_blinded.sh [-wblsdgt] [--numtoys 100] [--seed 42]
#
# Author: Raghav Kansal, adapted by Amitav Mitra
####################################################################################################

####################################################################################################
# Read options
####################################################################################################
workspace=0
bfit=0
limits=0
toylimits=0
significance=0
dfit=0
dfit_asimov=0
gofdata=0
goftoys=0
plotgof=0
impactsi=0
impactsf=0
impactsc=0
seed=42
numtoys=100
bias=-1
tf=0
tol=0.1  # --cminDefaultMinimizerTolerance
strat=1     # --cminDefaultMinimizerStrategy
rmin=-1
rmax=2
verbosity=2
robustFit=0

options=$(getopt -o "wblsdgti" --long "workspace,sig:,tf:,strat:,rmin:,rmax:,verbosity:,robustFit:,bfit,limits,significance,dfit,dfitasimov,toylimits,gofdata,goftoys,plotgof,impactsi,impactsf:,impactsc:,bias:,seed:,numtoys:,tol:" -- "$@")
eval set -- "$options"

while true; do
    case "$1" in
        -w|--workspace)
            workspace=1
            ;;
        --sig)
            shift 
            sig=$1
            ;;
        --tf)
            shift
            tf=$1
            ;;
        --strat)
            shift
            strat=$1
            ;;
        --rmin)
            shift
            rmin=$1
            ;;
        --rmax)
            shift
            rmax=$1
            ;;
        --verbosity)
            shift
            verbosity=$1
            ;;
        --robustFit)
            shift
            robustFit=$1
            ;;
        -b|--bfit)
            bfit=1
            ;;
        -l|--limits)
            limits=1
            ;;
        --toylimits)
            toylimits=1
            ;;
        -s|--significance)
            significance=1
            ;;
        -d|--dfit)
            dfit=1
            ;;
        --dfitasimov)
            dfit_asimov=1
            ;;
        -g|--gofdata)
            gofdata=1
            ;;
        -t|--goftoys)
            goftoys=1
            ;;
        --plotgof)
            plotgof=1
            ;;
        -i|--impactsi)
            impactsi=1
            ;;
        --impactsf)
            shift
            impactsf=$1
            ;;
        --impactsc)
            shift
            impactsc=$1
            ;;
        --bias)
            shift
            bias=$1
            ;;
        --seed)
            shift
            seed=$1
            ;;
        --numtoys)
            shift
            numtoys=$1
            ;;
        --tol)
            shift
            tol=$1
            ;;
        --)
            shift
            break;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
    shift
done

if [[ "$tf" == "" ]]; then
    printf "ERROR: must specify a transfer functions\n"
    exit 1
elif [[ "$sig" == "" ]]; then 
    printf "ERROR: must specify a signal via --sig\n"
    exit 1
fi

####################################################################################################
# Set up fit arguments. We use channel masking to mask either the SR or VR
# (mask = 1 means the channel is masked off)
####################################################################################################
dataset=data_obs
cards_dir="./${sig}_fits/NMSSM-XHY-${sig}-SR${tf}-VR${tf}_area/"
wsm="initialFitWorkspace"
wsm_snapshot=higgsCombineSnapshot.MultiDimFit.mH125
outsdir=${cards_dir}outs
cwd=$(pwd)

####################################################################################################
# Resonant X->HY->bbWW statistical test arguments
####################################################################################################
# Create lists of masked channels for SR and VR. For both, must specify non-masked channels as well.
# Will follow same naming convention as Raghav :(
# The easiest way to think about it is that the "blinded" region is the VR, where the Higgs mass window is blinded.
# Thus:
#       - "maskblindedargs" will contain args to mask the VR (blinded H mass region)
#       - "maskunblindedargs" will contain args to mask the SR (unblinded H mass region)

maskblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off

# Let's try unmasking the SR_fail so that it can be fit and obtain some initial QCD estimate there
maskunblindedargs="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_SR_pass_HIGH=1,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_fail_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,mask_VR_pass_HIGH=0" # SR entirely masked off (except SR fail)
#maskunblindedargs="mask_SR_fail_LOW=1,mask_SR_fail_SIG=1,mask_SR_fail_HIGH=1,mask_SR_pass_LOW=1,mask_SR_pass_SIG=1,mask_SR_pass_HIGH=1,mask_VR_fail_LOW=0,mask_VR_fail_SIG=0,mask_VR_fail_HIGH=0,mask_VR_pass_LOW=0,mask_VR_pass_SIG=0,mask_VR_pass_HIGH=0"   # SR (unblinded H mass region) entirely masked off 

# Here is another complication in the naming convention. 
# I think these are correct
#setparamsblinded="var{Background_SR.*}=0,rgx{Background_SR.*}=0"
setparamsblinded="var{Background_SR_pass.*}=0,rgx{Background_SR_pass.*}=0"
setparamsunblinded="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
#freezeparamsblinded="var{Background_SR.*},rgx{Background_SR.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
freezeparamsblinded="var{Background_SR_pass.*},rgx{Background_SR_pass.*},CMS_bbWW_PNetHbb_tag,CMS_bbWW_PNetWqq_tag"
freezeparamsunblinded="var{Background_VR.*},rgx{Background_VR.*}"
unblindedparams="--freezeParameters ${freezeparamsunblinded},var{.*_In},var{.*__norm},var{n_exp_.*} --setParameters ${maskblindedargs},${setparamsunblinded}"

####################################################################################################
# Combine cards, text2workspace, fit, limits, significances, fitdiagnositcs, GoFs
####################################################################################################
ulimit -s unlimited

if [ $workspace = 1 ]; then
    # First check if the 2DAlphabet workspace exists. It takes forever, so really check first
    if [ ! -d "./${sig}_fits/" ]; then 
        read -r -p "2DAlphabet workspace ./${sig}_fits/ for signal $sig and TF $tf does not exist. Do you want to make the workspace? [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                python VR.py --SRtf $tf --VRtf $tf -s $sig -w "${sig}_" --make --makeCard
                mkdir -p $outsdir
                (set -x; text2workspace.py "${cards_dir}card.txt" --channel-masks -o "${cards_dir}${wsm}.root") 2>&1 | tee outs/text2workspace.txt
                ;;
            *)
                printf "Exiting...\n"
                exit 1
                ;;
        esac
    else 
        # If the 2DAlphabet workspace exists, then just check if the cards and/or RooWorkspace for this TF exist
        if [ ! -d "${cards_dir}" ]; then 
            # Making the cards + RooWorkspace takes 2 seconds, so just do it here
            printf "Creating Combine card...\n"
            python VR.py --SRtf $tf --VRtf $tf -s $sig -w "${sig}_" --makeCard
            mkdir -p $outsdir
            printf "Creating RooWorkspace with channel masks...\n"
            (set -x; text2workspace.py "${cards_dir}card.txt" --channel-masks -o "${cards_dir}${wsm}.root") 2>&1 | tee outs/text2workspace.txt
        elif [ ! -f "{$cards_dir}{$wsm}.root" ]; then 
            # Making the RooWorkspace w/ channel masks takes 2 seconds, so just do it here
            mkdir -p $outsdir
            printf "Creating RooWorkspace with channel masks...\n"
            (set -x; text2workspace.py "${cards_dir}card.txt" --channel-masks -o "${cards_dir}${wsm}.root") 2>&1 | tee outs/text2workspace.txt
        fi
    fi
fi

# After workspace creation, we will cd to all card directories, so if the workspace doesn't exist we will get a warning beforehand. 

if [ $bfit = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    if [ ! -f "$wsm.root" ]; then 
        printf "RooWorkspace ${cards_dir}${wsm}.root does not exist, create it first with:\n\t./scripts/run_blinded.sh -w --tf $tf --sig $sig\n"
        exit 1
    else 
        mkdir -p $outsdir
        echo "Blinded background-only fit (MC Blinded)"
        (set -x; combine -D $dataset -M MultiDimFit --saveWorkspace -m 125 -d ${wsm}.root -v $verbosity \
        --cminDefaultMinimizerStrategy "$strat" --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 \
        --setParameters "${maskunblindedargs},${setparamsblinded},r=0"  \
        --robustFit $robustFit \
        --freezeParameters "r,${freezeparamsblinded}" --rMin "$rmin" --rMax "$rmax" -n Snapshot) 2>&1 | tee outs/MultiDimFit.txt
    fi
    cd $cwd
fi

if [ $limits = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    if [ ! -f "${wsm_snapshot}.root" ]; then 
        printf "Background-only fit snapshot ${cards_dir}${wsm_snapshot}.root does not exist, create it first with:\n\t./scripts/run_blinded.sh -wb --tf $tf --sig $sig\n"
        exit 1
    else 
        # Now we want to mask the VR and fit the SR, using the VR post-fit values stored in the MultiDimFit snapshot
        mkdir -p $outsdir
        echo "Expected limits (MC Unblinded)"
        (set -x; combine -M AsymptoticLimits -m 125 -n "" -d ${wsm_snapshot}.root --snapshotName MultiDimFit -v $verbosity \
        --saveWorkspace --saveToys --bypassFrequentistFit \
        ${unblindedparams},r=0 -s "$seed" \
        --floatParameters "${freezeparamsblinded},r" --toysFrequentist --run blind) 2>&1 | tee outs/AsymptoticLimits.txt
    fi
    cd $cwd
fi

if [ $significance = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    if [ ! -f "${wsm_snapshot}.root" ]; then 
        printf "Background-only fit snapshot ${cards_dir}${wsm}.root does not exist, create it first with:\n\t./scripts/run_blinded.sh -wb --tf $tf --sig $sig"
        exit 1
    else
        echo "Expected significance (MC Unblinded)"
        mkdir -p $outsdir
        (set -x; combine -M Significance -d ${wsm_snapshot}.root -n "" --significance -m 125 --snapshotName MultiDimFit -v $verbosity \
        -t -1 --expectSignal=1 --saveWorkspace --saveToys --bypassFrequentistFit \
        "${unblindedparams},r=1" \
        --floatParameters "${freezeparamsblinded},r" --toysFrequentist 2>&1) | tee outs/Significance.txt
    fi
    cd $cwd
fi


if [ $dfit = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    if [ ! -f "${wsm}.root" ]; then 
        printf "RooWorkspace ${cards_dir}${wsm}.root does not exist, create it first with:\n\t./scripts/run_blinded.sh -w --tf $tf --sig $sig\n"
        exit 1
    else
        echo "Fit Diagnostics (MC Blinded)"
        mkdir -p $outsdir
        (set -x; combine -M FitDiagnostics -m 125 -d ${wsm}.root \
        --setParameters "${maskunblindedargs},${setparamsblinded}" \
        --freezeParameters "${freezeparamsblinded}" --rMin "$rmin" --rMax "$rmax"\
        --cminDefaultMinimizerStrategy "$strat"  --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 \
        -n Blinded --ignoreCovWarning -v $verbosity 2>&1) | tee outs/FitDiagnostics.txt

        echo "Fit Shapes"
        (set -x; PostFitShapesFromWorkspace --dataset "$dataset" -w ${wsm}.root --output FitShapes.root \
        -m 125 -f fitDiagnosticsBlinded.root:fit_b --postfit --print) 2>&1 | tee outs/FitShapes.txt
    fi
    cd $cwd
fi

if [ $dfit_asimov = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir

    echo "Fit Diagnostics on Asimov dataset (MC Unblinded)"
    mkdir -p $outsdir
    (set -x; combine -M FitDiagnostics -m 125 -d ${wsm_snapshot}.root --snapshotName MultiDimFit \
    -t -1 --expectSignal=1 --toysFrequentist --bypassFrequentistFit --saveWorkspace --saveToys \
    "${unblindedparams}" --floatParameters "${freezeparamsblinded},r" --rMin "$rmin" --rMax "$rmax"\
    --cminDefaultMinimizerStrategy "$strat"  --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 \
    -n Asimov --ignoreCovWarning -v $verbosity) 2>&1 | tee outs/FitDiagnosticsAsimov.txt

    (set -x; combineTool.py -M ModifyDataSet ${wsm}.root:w ${wsm}_asimov.root:w:toy_asimov -d higgsCombineAsimov.FitDiagnostics.mH125.123456.root:toys/toy_asimov) 2>&1 | tee outs/ModifyDataSetAsimov.txt

    echo "Fit Shapes"
    (set -x; PostFitShapesFromWorkspace --dataset toy_asimov -w ${wsm}_asimov.root --output FitShapesAsimov.root \
    -m 125 -f fitDiagnosticsAsimov.root:fit_b --postfit --print) 2>&1 | tee outs/FitShapesAsimov.txt

    cd $cwd
fi

if [ $gofdata = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "GoF on data"
    (set -x; combine -M GoodnessOfFit -d ${wsm_snapshot}.root --algo saturated -m 125 \
    --snapshotName MultiDimFit --bypassFrequentistFit \
    --setParameters "${maskunblindedargs},${setparamsblinded},r=0" \
    --freezeParameters "${freezeparamsblinded},r" \
    --cminDefaultMinimizerStrategy "$strat"  --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 \
    -n Data -v $verbosity) 2>&1 | tee outs/GoF_data.txt
    cd $cwd
fi


if [ $goftoys = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "GoF on toys"
    (set -x; combine -M GoodnessOfFit -d ${wsm_snapshot}.root --algo saturated -m 125 \
    --snapshotName MultiDimFit --bypassFrequentistFit \
    --setParameters "${maskunblindedargs},${setparamsblinded},r=0" \
    --freezeParameters "${freezeparamsblinded},r" --saveToys \
    --cminDefaultMinimizerStrategy "$strat"  --cminDefaultMinimizerTolerance "$tol" --X-rtd MINIMIZER_MaxCalls=400000 \
    -n Toys -v $verbosity -s "$seed" \
    -t "$numtoys" --toysFrequentist) 2>&1 | tee outs/GoF_toys.txt
    cd $cwd
fi

if [ $plotgof = 1 ]; then 
    if [ ! -f "${cards_dir}higgsCombineData.GoodnessOfFit.mH125.root" ]; then 
        printf "ERROR: GoF data file ${cards_dir}higgsCombineData.GoodnessOfFit.mH125.root missing - run GoF on data first:\n\t./scripts/run_blinded.sh --sig $sig --tf $tf -g [--verbosity,--strat,--tol]\n"
        exit 1
    elif [ ! -f "${cards_dir}higgsCombineToys.GoodnessOfFit.mH125.${seed}.root" ]; then 
        printf "ERROR: GoF toys file ${cards_dir}higgsCombineToys.GoodnessOfFit.mH125.${seed}.root missing - run GoF on toys first:\n\t./scripts/run_blinded.sh --sig $sig --tf $tf -t [--verbosity,--strat,--tol,--numtoys]\n"
        exit 1
    fi
    (set -x; python scripts/plot_gof.py -w $cards_dir -s $seed) 2>&1 | tee "${outsdir}/GoF_toys.txt"
fi


if [ $impactsi = 1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "Initial fit for impacts"
    (set -x; combineTool.py -M Impacts --snapshotName MultiDimFit -m 125 -n "impacts" \
    -t -1 --bypassFrequentistFit --toysFrequentist --expectSignal 1 \
    -d ${wsm_snapshot}.root --doInitialFit  --rMin $rmin --rMax $rmax \
    ${unblindedparams} --floatParameters ${freezeparamsblinded} \
     --cminDefaultMinimizerStrategy=$strat --cminDefaultMinimizerTolerance "$tol" \
     --X-rtd MINIMIZER_MaxCalls=400000 \
     -v $verbosity) 2>&1 | tee outs/Impacts_init.txt
     cd $cwd
fi

# For this, you have to pass the parameters to the script. You can do all of them like so:
#   params=`python scripts/get_parameters_for_impacts.py`
#   for p in $params; do ./scripts/run_blinded.sh --sig <SIG> --tf <TF> --tol <TOL> --strat <STRAT> --verbosity <VERBOSITY> --impactsf $p; done 
# Or just pass the parameters manually. 
if [ "$impactsf" != 0 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "Impact scan for $impactsf"
    # Impacts module cannot access parameters which were frozen in MultiDimFit, so running impacts here for each parameter directly using its internal command (also need to do this for submitting to condor anywhere other than lxplus)
    (set -x; combine -M MultiDimFit -n "_paramFit_impacts_$impactsf" -d ${wsm_snapshot}.root \
    --algo impact --redefineSignalPOIs r -P "$impactsf" --floatOtherPOIs 1 --saveInactivePOI 1 \
    --snapshotName MultiDimFit -t -1 --bypassFrequentistFit --toysFrequentist --expectSignal 1 \
    ${unblindedparams} --floatParameters ${freezeparamsblinded} --setParameterRanges r=-0.5,20 \
    --cminDefaultMinimizerStrategy=$strat --cminDefaultMinimizerTolerance "$tol" \
    --X-rtd MINIMIZER_MaxCalls=400000 -v $verbosity -m 125) | tee "outs/Impacts_$impactsf.txt" 
    cd $cwd
fi

if [ "$impactsc" != 0 ]; then
    # First get all of the parameters
    named=""
    named_params=`python scripts/get_parameters_for_impacts.py`
    for p in $named_params; do
        named+="${p},"
    done
    named=${named%,} # get rid of trailing comma
    printf "Tracking all impacts: ${named}\n"
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "Collecting impacts"
    (set -x; combineTool.py -M Impacts --snapshotName MultiDimFit \
    -m 125 -n "impacts" -d ${wsm_snapshot}.root \
    --setParameters "${maskblindedargs}" --floatParameters "${freezeparamsblinded}" \
    -t -1 --named "$named" \
    --setParameterRanges r=-0.5,20 -v $verbosity -o impacts.json) 2>&1 | tee outs/Impacts_collect.txt

    plotImpacts.py -i impacts.json -o impacts
    cd $cwd
fi

if [ "$bias" != -1 ]; then
    printf "cd $cards_dir \n"
    cd $cards_dir
    echo "Bias test with bias $bias"
    # setting verbose > 0 here can lead to crazy large output files (~10-100GB!) because of getting stuck in negative yield areas
    (set -x; combine -M FitDiagnostics --trackParameters r --trackErrors r --justFit \
    -m 125 -n "bias${bias}" -d ${wsm_snapshot}.root --rMin "$rmin" --rMax "$rmax" \
    --snapshotName MultiDimFit --bypassFrequentistFit --toysFrequentist --expectSignal "$bias" \
    ${unblindedparams},r=$bias --floatParameters ${freezeparamsblinded} \
     -t "$numtoys" -s "$seed" -v 0 \
    --X-rtd MINIMIZER_MaxCalls=1000000 --cminDefaultMinimizerTolerance "$tol" 2>&1) | tee "outs/bias${bias}seed${seed}.txt"
    cd $cwd
fi

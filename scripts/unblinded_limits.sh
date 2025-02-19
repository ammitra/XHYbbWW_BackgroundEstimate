#!/bin/bash

# Fit options
tf=0
rmax=2
strat=0
tol=0.1
verbosity=2
robustFit=0
seed=123456
# Methods
workspace=0
bfit=0
dfit=0
limits=0
significance=0

options=$(getopt -o "wbdls" --long "sig:,tf:,rmax:,strat:,tol:,verbosity:,robustFit,workspace,bfit,dfit,limits,significance" -- "$@")
eval set -- "$options"

while true; do 
    case "$1" in 
        --sig)
            shift
            sig=$1
            ;;
        --tf)
            shift 
            tf=$1
            ;;
        --rmax)
            shift
            rmax=$1
            ;;
        --strat)
            shift
            strat=$1
            ;;
        --tol)
            shift
            tol=$1
            ;;
        --verbosity)
            shift 
            verbosity=$1
            ;;
        --robustFit)
            robustFit=1
            ;;
        -w|--workspace)
            workspace=1
            ;;
        -b|--bfit)
            bfit=1
            ;;
        -d|--dfit)
            dfit=1
            ;;
        -l|--limits)
            limits=1
            ;;
        -s|--significance)
            significance=1
            ;;
        --)
            shift
            break;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            return
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            return
            ;;
    esac
    shift
done

if [[ "$tf" == "" ]]; then
    printf "ERROR: must specify a transfer functions\n"
    return
elif [[ "$sig" == "" ]]; then 
    printf "ERROR: must specify a signal via --sig\n"
    return
fi

######################################################
# Set up fits                                        #
######################################################
cards_dir="./${sig}_fits/Unblinded_${tf}/"
wsm="workspace_masked"
wsm_snapshot="higgsCombineSnapshot.MultiDimFit.mH125"
outsdir="${cards_dir}outs"
cwd=$(pwd)

######################################################
# Channel masking. We want to mask the VR.           #
######################################################
maskVR="mask_SR_fail_LOW=0,mask_SR_fail_SIG=0,mask_SR_fail_HIGH=0,mask_SR_pass_LOW=0,mask_SR_pass_SIG=0,mask_SR_pass_HIGH=0,mask_VR_fail_LOW=1,mask_VR_fail_SIG=1,mask_VR_fail_HIGH=1,mask_VR_pass_LOW=1,mask_VR_pass_SIG=1,mask_VR_pass_HIGH=1"   # VR (blinded H mass region) entirely masked off
setVR="var{Background_VR.*}=0,rgx{Background_VR.*}=0"
freezeVR="var{Background_VR.*},rgx{Background_VR.*}"

#####################################################
# Methods                                           #
#####################################################
ulimit -s unlimited

if [ $workspace = 1 ]; then 
    if [ ! -d $cards_dir ]; then 
        echo "#####################################################"
        echo "Making unblinded workspace for ${sig}, ${tf}"
        python VR.py --SRtf $tf --VRtf $tf -s $sig -w "${sig}_" --makeCardUnblinded
        echo "Creating RooWorkspace with channel masks..."
        mkdir -p $outsdir
        (set -x; text2workspace.py "${cards_dir}card.txt" --channel-masks -o "${cards_dir}${wsm}.root")
        echo "#####################################################"
    fi 
fi

if [ $bfit = 1 ]; then 
    printf "cd $cards_dir \n"
    cd $cards_dir
    if [ ! -f "$wsm.root" ]; then 
        echo "$wsm.root does not exist. Create it with: ./scripts/run_unblinded.sh -w --tf $tf --sig $sig"
    else
        mkdir -p $outsdir
        echo "Unblinded background-only fit....."
        (set -x; combine -D data_obs -M MultiDimFit --saveWorkspace -m 125 -d ${wsm}.root -v $verbosity --cminDefaultMinimizerStrategy $strat --cminDefaultMinimizerTolerance $tol --X-rtd MINIMIZER_MaxCalls=400000 --setParameters "${maskVR},${setVR},r=0" --robustFit $robustFit --freezeParameters "r,${freezeVR}" --rMin -1 --rMax $rmax -n Snapshot) 2>&1 | tee outs/MultiDimFit_bonly.txt
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
        echo "Fit Diagnostics...."
        mkdir -p $outsdir
        (set -x; combine -M FitDiagnostics -m 125 -d ${wsm}.root \
        --setParameters "${maskVR},${setVR}" --freezeParameters "${freezeVR}" --rMin -1 --rMax $rmax --cminDefaultMinimizerStrategy $strat  --cminDefaultMinimizerTolerance $tol --X-rtd MINIMIZER_MaxCalls=400000 -n Unblinded --ignoreCovWarning -v $verbosity) 2>&1 | tee outs/FitDiagnostics.txt

        echo "2D Fit Shapes"
        (set -x; PostFit2DShapesFromWorkspace --dataset data_obs -w ${wsm}.root --output FitShapes.root -m 125 -f fitDiagnosticsUnblinded.root:fit_b --postfit --print) 2>&1 | tee outs/FitShapes.txt
    fi
    cd $cwd
fi

if [ $limits = 1 ]; then 
    echo "Limits"
    cd $cards_dir
    (set -x; combine -M AsymptoticLimits -m 125 -n "" -d $wsm.root -v $verbosity --rMax $rmax --saveWorkspace --saveToys -s "$seed" --toysFrequentist --setParameters "${maskVR},${setVR}" --freezeParameters "${freezeVR}") 2>&1 | tee $outsdir/AsymptoticLimits.txt
    cd $cwd
fi

if [ $significance = 1 ]; then
    echo "Significance"
    cd $cards_dir
    (set -x; combine -M Significance -m 125 -n "" -d $wsm.root -v $verbosity --rMax $rmax --saveWorkspace --saveToys -s "$seed" --toysFrequentist) 2>&1 | tee $outsdir/Significance.txt
    cd $cwd
fi
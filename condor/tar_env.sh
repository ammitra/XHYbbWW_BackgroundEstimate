#!/bin/bash

# This script sends over the CMSSW environment with the compiled Combine

cd $CMSSW_BASE/../
    tar --exclude-caches-all --exclude-vcs -cvzf CMSSW_14_1_0_pre4_env.tgz \
    --exclude=tmp --exclude=".scram" --exclude=".SCRAM" \
    --exclude=CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/docs \
    --exclude=CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/data/benchmarks \
    --exclude=CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/data/tutorials \
    --exclude=CMSSW_14_1_0_pre4/src/2DAlphabet \
    --exclude=CMSSW_14_1_0_pre4/src/XHYbbWW \
    --exclude=CMSSW_14_1_0_pre4/src/Tprime \
    --exclude=CMSSW_14_1_0_pre4/src/for_tamas \
    --exclude=CMSSW_14_1_0_pre4/src/twoD-env \
    CMSSW_14_1_0_pre4
xrdcp -f CMSSW_14_1_0_pre4_env.tgz root://cmseos.fnal.gov//store/user/$USER/
cd $CMSSW_BASE/src/XHYbbWW

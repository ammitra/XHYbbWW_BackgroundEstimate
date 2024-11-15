'''
Compare the postfit nuisances b/w the FitDiagnostics and the MultiDimFit
'''

import ROOT

fDiag  = ROOT.TFile.Open("1800-1200_fits/NMSSM-XHY-1800-1200-SR1x0-VR1x0_area/fitDiagnosticsBlinded.root","READ")
fMulti = ROOT.TFile.Open("1800-1200_fits/NMSSM-XHY-1800-1200-SR1x0-VR1x0_area/higgsCombineSnapshot.MultiDimFit.mH125.root","READ")
fitb   = fDiag.Get("fit_b")
wMulti = fMulti.Get("w")

# Get all parameter final values from the FitDiagnosticsTest
pars = fitb.floatParsFinal()
par_values = {}
for par in pars:
    par_values[str(par.getTitle())] = [par.getVal(),par.getError()]

# get all parameter final values from MultiDimFit 
snap = wMulti.getSnapshot('MultiDimFit')
md_vals = {}
for param in ['Background*','CMS_*','ps_*','lumi*','QCD*']:
    snapshot = snap.selectByName(param,True)
    iterator = snapshot.createIterator()
    var = iterator.Next()
    while var:
        if not isinstance(var,ROOT.RooRealVar): var = iterator.Next()
        md_vals[str(var.GetName())] = [var.getVal(), var.getError()]
        var = iterator.Next()

# print(md_vals)
# print('++++++++++++++++++++++++++++++++++++++++++')
# print(par_values)

# Now compare the two 
out = open('Compare_MultiDimFit_and_FitDiagnostics_Bonly.txt','w')
for k,v in md_vals.items():
    if k not in par_values: continue
    val_mult = v[0]
    val_diag = par_values[k][0]
    print('----------------------------------------------------------------------------------------')
    print(f'MultiDimFit:    {k} = {v[0]} +/- {v[1]}')
    print(f'FitDiagnostics: {k} = {par_values[k][0]} +/- {par_values[k][1]}')
    print(f'\tDifference = {round(abs(1.-(val_diag/val_mult))*100,2)}%')
    out.write('----------------------------------------------------------------------------------------\n')
    out.write(f'MultiDimFit:    {k} = {v[0]} +/- {v[1]}\n')
    out.write(f'FitDiagnostics: {k} = {par_values[k][0]} +/- {par_values[k][1]}\n')
    out.write(f'\tDifference = {round(abs(1.-(val_diag/val_mult))*100,2)}%\n')
    if (abs(1.-(val_diag/val_mult)) > 0.03) or (abs(1.-(val_mult/val_diag)) > 0.03):
        print(f'WARNING: {k} : MultiDimFit and FitDiagnostics differ by > 3%')
        print(f'\tDifference = {round(abs(1.-(val_diag/val_mult))*100,2)}%')
        out.write(f'WARNING: {k} : MultiDimFit and FitDiagnostics differ by > 3%\n')
        out.write(f'\tDifference = {round(abs(1.-(val_diag/val_mult))*100,2)}%\n')
out.close()
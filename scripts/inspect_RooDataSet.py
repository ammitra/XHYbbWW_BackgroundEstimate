'''
Script to look at the RooAbsData objects in a file and print out the sums.
'''
import ROOT

# Get the file
fname = '4000-2000_fits/NMSSM-XHY-4000-2000-SR1x0-VR1x0_area/higgsCombineSnapshot.MultiDimFit.mH120.root'
f = ROOT.TFile.Open(fname,'READ')



# This file has a RooWorkspace containing many RooDataSets. Get the workspace
w = f.Get('w')
# Let's look at the RooDataSets. First, grab them
# https://root.cern.ch/doc/master/classRooWorkspace.html#aa1c2535c5971897fbeab1ee27bfa4f71
'''
allDataSets = w.allData()
# Now loop over them.
for dataset in allDataSets:
    name 	= dataset.GetName() # Get RooDataSet name
    sumEntries  = dataset.sumEntries()  # Get RooDataSet summed entries
    print('Dataset: {}\nsum:{}'.format(name,sumEntries))

    # you can also print the dataset contents directly using RooDataSet::Print()
    dataset.Print("V")
'''

allvars = w.allVars()
for var in allvars:
    print(var)

allfuncs = w.allFunctions()
for f in allfuncs:
    print(f)

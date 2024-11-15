'''
Script to determine which of the signal masses do not have all 4 years generated.
This can be determined by finding which of the fit dirs does not have "base.root"
'''
import subprocess, os, json 

sigs_missing = {} # signals that need to be produced centrally
f_redo = open('sigs_to_redo.txt','w') # signals that are messed up and only missing a file or two for some reason

for mx in [4000,3500,3000,2800,2600,2500,2400,2200,2000,1800,1600,1400,1200,1000,900,800,700,600,500,400,360,320,300,280,240]:
    for my in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]:
        # Determine if the mass point is kinematically allowed
        if not (mx >= my + 125):
            continue 
        else:
            # Check if file exists
            if not os.path.isfile(f'{mx}-{my}_fits/base.root'):
                try:
                    files = subprocess.check_output(f'eosls /store/user/ammitra/XHYbbWW/selection | grep {mx}-{my}_',shell=True,text=True).split()
                    # First check if the signal is missing an entire year, or some bug happened 
                    nFiles = len(files)
                    if nFiles % 9: # There are 8 variations + 1 nominal file = 9 template files per year, so if the signal is missing a year the number of files should still be divisible by 9
                        print(f'[TEMPLATE-MAKING ERROR] - Signal mass point {mx}-{my} has {nFiles} templates')
                        f_redo.write(f'{mx}-{my}\n')
                    else:
                        years = [i.split('_')[2].replace('.root','') for i in files]
                        unique_years = set(years)
                        valid_years = set(['16APV','16','17','18'])
                        missing = list(valid_years - unique_years)
                        print(f'Signal mass point {mx}-{my} is missing files for year(s):')
                        for m in missing:
                            print(f'\t 20{m}')
                        sigs_missing[f'{mx}-{my}'] = missing 
                except: 
                    print(f'Signal mass point {mx}-{my} is missing files for ALL years')
                    sigs_missing[f'{mx}-{my}'] = ['16APV','16','17','18']

f_redo.close()
with open('sigs_missing.json', 'w') as fp:
    json.dump(sigs_missing, fp, indent=4)
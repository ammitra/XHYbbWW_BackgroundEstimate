from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import TwoDAlphabet

dir = '1800-1200_fits'
twoD = TwoDAlphabet(dir,f'{dir}/runConfig.json',loadPrevious=True)
plot.make_systematic_plots(twoD)
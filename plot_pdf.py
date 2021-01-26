import os
import re
import ROOT as r
from matplotlib import pyplot as plt

# Run ROOT in batch mode (no graphic display)
r.gROOT.SetBatch(True)

pjoin = os.path.join

prior_ht_bins = [
    '0_to_200',
    '200_to_400',
    '400_to_600',
    '600_to_800',
    '800_to_1000',
    '1000_to_2000',
    '2000_to_5000',
]

def main():
    # Input file for distributions
    rfile = './input/htmiss_prior.root'
    f = r.TFile(rfile)
    
    htmiss_variable = r.RooRealVar('gen_htmiss_pt', 'gen_htmiss_pt', 0, 500)

    outdir = './output/interpolated_priors'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for key in f.GetListOfKeys():
        hist = key.ReadObj()
        histname = hist.GetName()

        ht_bin = re.findall('\d+_to_\d+', histname)[0]
        year = re.findall('201\d', histname)[0]

        datahist = r.RooDataHist('h_prior_pdf', 'h_prior_pdf', r.RooArgList(htmiss_variable), hist)

        prior_pdf = r.RooHistPdf('prior_pdf', 'prior_pdf', r.RooArgSet(htmiss_variable), datahist)
        # Quadratic interpolation
        prior_pdf.setInterpolationOrder(2)

        # Plot the PDF and save figure
        htframe = htmiss_variable.frame(0,500)
        prior_pdf.plotOn(htframe)

        c = r.TCanvas('prior_pdf', 'prior_pdf')
        htframe.Draw()
        outpath = pjoin(outdir, f'interpolated_prior_{ht_bin}_{year}.png')
        c.SaveAs(outpath)

if __name__ == '__main__':
    main()
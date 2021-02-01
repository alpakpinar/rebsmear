#!/usr/bin/env python

import os
import sys
import re
import glob
import ROOT as r
import mplhep as hep
from matplotlib import pyplot as plt
from pprint import pprint

pjoin = os.path.join

def htmiss_func_name():
    return 'gen_htmiss_pt'

def save_htmiss_before_and_after(infiles, outdir):
    '''Save the HTmiss histograms before and after rebalancing, using the list of provided input files.'''
    # Initialize two ROOT histograms (before/after)
    h_bef = r.TH1F('htmiss_before', r'$H_T^{miss} \ (GeV)$', 50, 0, 500)
    h_aft = r.TH1F('htmiss_after', r'$H_T^{miss} \ (GeV)$', 50, 0, 500)

    for infile in infiles:
        print(f'Reading events from file: {infile}')
        f = r.TFile(infile)

        keys = f.GetListOfKeys()
        nkeys = len(keys)

        for idx in range(nkeys):
            if idx % 200 == 0 and idx > 0:
                print(f'Reading entry: {idx}')
            
            name = keys[idx].GetName()
            if name.startswith('ProcessID'):
                continue

            ws = f.Get(name)
            # Extract the HTmiss value  out of the workspace
            htmiss = ws.function(htmiss_func_name()).getValV()

            if name.startswith('before'):
                h_bef.Fill(htmiss)
            elif name.startswith('rebalanced'):
                h_aft.Fill(htmiss)

    # Once we're done filling the histogram with all the events, save the two histograms to a new ROOT file
    outpath = pjoin(outdir, 'htmiss_after_reb.root')
    outf = r.TFile(outpath, 'RECREATE')

    outf.cd()
    h_bef.Write()
    h_aft.Write()

    print(f'Histograms saved to: {outpath}')

def main():
    # Point the script to the directory containing the workspace files
    inpath = sys.argv[1]
    infiles = glob.glob(pjoin(inpath, 'ws_eventchunk*.root'))

    jobtag = re.findall('202\d.*', inpath)[0].split('/')[0]

    # Output directory for plotting
    outdir = f'./output/{jobtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Save histograms to ROOT file
    save_htmiss_before_and_after(infiles, outdir)

if __name__ == '__main__':
    main()
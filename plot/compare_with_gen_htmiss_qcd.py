#!/usr/bin/env python

import os
import sys
import re
import uproot
import numpy as np
import mplhep as hep

from matplotlib import pyplot as plt
from coffea.util import load
from coffea import hist
from pprint import pprint

pjoin = os.path.join

def compare_with_genhtmiss_dist(acc, jobtag, inputrootfile):
    '''Compare the GEN-level HTmiss distribution with the HTmiss distribution coming from rebalancing.'''
    h = acc['gen_htmiss']

    # Get all the events
    h = h.integrate('dataset').integrate('region', 'inclusive')

    h_from_reb = inputrootfile['htmiss_after']

    fig, ax = plt.subplots()
    hep.histplot(h_from_reb.values, h_from_reb.edges, ax=ax, label='From rebalancing')

    hist.plot1d(h, ax=ax, clear=False)

    # Save figure
    outdir = f'./output/{jobtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'htmiss_comp.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def main():
    # Input ROOT file
    inputrootpath = sys.argv[1]
    inputrootfile = uproot.open(inputrootpath)
    # Input coffea file for GEN-level HTmiss distribution
    acc = load('./input/qcd_QCD_HT700to1000-mg_new_pmx_2017.coffea')

    jobtag = re.findall('202\d.*', inputrootpath)[0].split('/')[0]

    compare_with_genhtmiss_dist(acc, jobtag, inputrootfile)

if __name__ == '__main__':
    main()

#!/usr/bin/env python

import os
import sys
import re
import uproot
import mplhep as hep
from matplotlib import pyplot as plt
from pprint import pprint

pjoin = os.path.join

def plot_htmiss_before_and_after(outdir, infile):
    '''Do the actual plotting of distributions.'''
    f = uproot.open(infile)
    htmiss_bef = f['htmiss_before']
    htmiss_aft = f['htmiss_after']

    fig, ax = plt.subplots()

    hep.histplot(htmiss_bef.values, htmiss_bef.edges, ax=ax, label='Before')
    hep.histplot(htmiss_aft.values, htmiss_aft.edges, ax=ax, label='After')

    ax.set_xlabel(r'$H_T^{miss} \ (GeV)$', fontsize=14)
    ax.set_ylabel(r'Counts', fontsize=14)

    ax.legend(title='Rebalancing')

    ax.text(0., 1., 'JetHT 2017',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outpath = pjoin(outdir, f'htmiss_before_after_reb.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def main():
    # Point the script to the ROOT file containing before/after histograms
    infile = sys.argv[1]

    # Output directory for plotting
    outdir = './output'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    plot_htmiss_before_and_after(outdir, infile=infile)

if __name__ == '__main__':
    main()
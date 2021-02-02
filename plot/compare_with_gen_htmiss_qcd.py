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

def compare_with_genhtmiss_dist(acc, jobtag, inputrootfile, logy=False):
    '''Compare the GEN-level HTmiss distribution with the HTmiss distribution coming from rebalancing.'''
    h = acc['gen_htmiss']

    # Get all the events
    h = h.integrate('dataset').integrate('region', 'inclusive')

    h_from_reb = inputrootfile['htmiss_after']

    fig, ax = plt.subplots()
    hep.histplot(h_from_reb.values, h_from_reb.edges, ax=ax, label='From rebalancing')

    hist.plot1d(h, ax=ax, clear=False)

    if logy:
        ax.set_yscale('log')
        ax.set_ylim(1e-2,1e6)

    # Number of events we're comparing, no weights!
    nevents = np.sum(h_from_reb.values)

    ax.text(0., 1., f'{nevents:.0f} events, QCD MC',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels):
        if label == 'None':
            handle.set_label('From QCD MC (GEN)')

    ax.legend(handles=handles)

    # Save figure
    outdir = f'./output/{jobtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if logy:
        outpath = pjoin(outdir, f'htmiss_comp_logy.pdf')
    else:
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
    compare_with_genhtmiss_dist(acc, jobtag, inputrootfile, logy=True)

if __name__ == '__main__':
    main()

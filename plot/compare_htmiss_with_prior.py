#!/usr/bin/env python

import os
import sys
import re
import numpy as np
import uproot

from coffea.util import load
from coffea import hist
from matplotlib import pyplot as plt
from pprint import pprint

pjoin = os.path.join

def compare_htmiss_with_prior(acc, f, region='inclusive', htwindow='700_to_900'):
    '''Compare the prior with the HTmiss distribution from the accumulator.'''
    h = acc['htmiss_ht']
    h = h.integrate('dataset').integrate('region', region)

    # Get events within the HT window we're looking for
    lo, hi = map(int, re.findall('\d+', htwindow))
    h_withhtcut = h.integrate('ht', slice(lo, hi))
    h_withouthtcut = h.integrate('ht')

    # Scale the histograms
    h_withhtcut.scale(
        1/np.sum(h_withhtcut.values()[()])
        )
    h_withouthtcut.scale(
        1/np.sum(h_withouthtcut.values()[()])
        )

    # Get the prior we want
    prior = f[f'gen_htmiss_ht_{htwindow}']

    xcenters = 0.5 * np.sum(prior.bins, axis=1)

    fig, ax = plt.subplots()
    hist.plot1d(h_withhtcut, ax=ax)
    hist.plot1d(h_withouthtcut, ax=ax, clear=False)
    ax.plot(xcenters, prior.values)

    ax.set_yscale('log')
    ax.set_ylim(1e-8,1e0)
    ax.set_xlim(0,500)

    ax.legend(labels=[r'QCD MC, with $H_T^{gen}$ cut', r'QCD MC, without $H_T^{gen}$ cut', 'Prior'])

    ax.text(0.,1.,f'${lo} < H_T < {hi}$',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    # Save figure
    outdir = './output'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, 'prior_htmiss_comp.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def main():
    # Input path to the coffea file, where we will extract the HTmiss distribution
    inpath = sys.argv[1]
    acc = load(inpath)

    # Input root file for priors
    rootpath = '../input/htmiss_prior.root'
    f = uproot.open(rootpath)

    compare_htmiss_with_prior(acc, f)

if __name__ == '__main__':
    main()

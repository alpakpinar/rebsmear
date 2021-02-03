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

def compare_with_genhtmiss_dist(acc, distribution, jobtag, filetag, inputrootfile, logy=False):
    '''Compare the GEN-level HTmiss distribution with the HTmiss distribution coming from rebalancing.'''
    h = acc[distribution]

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

    ax.text(1., 1., filetag,
        fontsize=14,
        ha='right',
        va='bottom',
        transform=ax.transAxes
    )

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels):
        if label == 'None':
            handle.set_label('QCD MC (GEN)')

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

def comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag, logy=False):
    '''Compare GEN-HTmiss distribution with the priors we use as input to rebalancing.'''
    h = acc[distribution]
    # Get all the events
    h = h.integrate('dataset').integrate('region', 'inclusive')

    # Plot the GEN HT-miss distribution from coffea 
    fig, ax = plt.subplots()
    # Normalize
    total_sumw = np.sum(h.values()[()])
    h.scale(1/total_sumw)
    hist.plot1d(h, ax=ax, binwnorm=1)

    # Read and plot the priors from the input file
    inputpriorfile = uproot.open('../input/htmiss_prior.root')
    ht_bins_for_prior = [
        '700_to_900',
        '900_to_1300',
    ]

    def label_for_htbin(htbin):
        lo, hi = re.findall('\d+', htbin)
        return f'Prior: {lo} < $H_T$ < {hi}'

    for htbin in ht_bins_for_prior:
        ph = inputpriorfile[f'gen_htmiss_ht_{htbin}']
        binw = np.diff(ph.edges)
        hep.histplot(ph.values / binw, ph.edges, ax=ax, label=label_for_htbin(htbin))

    ax.set_xlim(0,500)
    if logy:
        ax.set_yscale('log')
        ax.set_ylim(1e-8,1e0)

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels):
        if label == 'None':
            handle.set_label('GEN $H_T^{miss}$ from QCD MC \n ($700 < H_T < 1000 \ GeV$)')

    ax.legend(handles=handles)
    ax.set_ylabel('Normalized Yields')

    # Save figure
    outdir = f'./output/{jobtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if logy:
        outpath = pjoin(outdir, f'prior_htmiss_comp_logy.pdf')
    else:
        outpath = pjoin(outdir, f'prior_htmiss_comp.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def main():
    # Input ROOT file
    inputrootpath = sys.argv[1]
    inputrootfile = uproot.open(inputrootpath)
    jobtag = re.findall('202\d.*', inputrootpath)[0].split('/')[0]

    # Input coffea file for GEN-level HTmiss distribution
    coffeapath = './input/qcd_QCD_HT700to1000-mg_new_pmx_2017.coffea'
    acc = load(coffeapath)

    filetag = re.findall('HT\d+to\d+', coffeapath)[0]

    # The distribution to look at
    distribution = 'gen_htmiss_noweight'

    compare_with_genhtmiss_dist(acc, distribution, jobtag, filetag, inputrootfile)
    compare_with_genhtmiss_dist(acc, distribution, jobtag, filetag, inputrootfile, logy=True)

    # Compare priors with GEN-level HTmiss we obtain
    comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag)
    comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag, logy=True)

if __name__ == '__main__':
    main()

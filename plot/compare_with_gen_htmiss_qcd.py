#!/usr/bin/env python

import os
import sys
import re
import uproot
import argparse
import numpy as np
import mplhep as hep

from matplotlib import pyplot as plt
from coffea.util import load
from coffea import hist
from bucoffea.plot.util import merge_datasets, merge_extensions, scale_xs_lumi
from klepto.archives import dir_archive
from pprint import pprint

pjoin = os.path.join

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', help='Path to root file containing distributions from rebalancing.')
    parser.add_argument('--coffea', help='Path to coffea accumulator containing distributions from QCD MC.')
    parser.add_argument('--compare_with_fullacc', help='Compare with the distribution from full accumulator.', action='store_true')
    args = parser.parse_args()
    return args

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

    ax.set_xlim(0,500)

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

def comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag, logy=False, acc_large=None):
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

    # Accumulator with the set of whole trees 
    # (Instead of a single tree), if provided
    if acc_large is not None:
        acc_large.load(distribution)
        h_large = acc_large[distribution]

        h_large = merge_extensions(h_large, acc_large, reweight_pu=False)
        scale_xs_lumi(h_large)
        h_large = merge_datasets(h_large)

        h_large = h_large.integrate('dataset').integrate('region', 'inclusive')

        total_sumw = np.sum(h_large.values()[()])
        h_large.scale(1/total_sumw)
        hist.plot1d(h_large, ax=ax, binwnorm=1, clear=False)

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

    new_labels = [
        'GEN $H_T^{miss}$ from QCD MC \n($700 < H_T < 1000 \ GeV$, single tree)',
        'GEN $H_T^{miss}$ from QCD MC \n($700 < H_T < 1000 \ GeV$, all trees combined)',
    ]

    handles, labels = ax.get_legend_handles_labels()
    for idx, (handle, label) in enumerate(zip(handles, labels)):
        if label == 'None':
            handle.set_label(new_labels[idx-2])

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
    args = parse_cli()
    if not (args.coffea and args.root):
        raise RuntimeError('Please provide --coffea and --root arguments as inputs.')
    
    # Input ROOT file
    inputrootpath = args.root
    inputrootfile = uproot.open(inputrootpath)
    jobtag = re.findall('202\d.*', inputrootpath)[0].split('/')[0]

    # Input coffea file for GEN-level HTmiss distribution
    coffeapath = args.coffea
    acc = load(coffeapath)

    # Accumulator with the whole set of trees for 700 < HT < 1000
    if args.compare_with_fullacc:
        acc_large = dir_archive('./input/merged_2021-02-03_qcd_test_HT-700_to_1000')
        acc_large.load('sumw')
        acc_large.load('sumw2')
    else:
        acc_large = None

    filetag = re.findall('HT\d+to\d+', coffeapath)[0]

    # The distribution to look at
    distribution = 'gen_htmiss_noweight'

    compare_with_genhtmiss_dist(acc, distribution, jobtag, filetag, inputrootfile)
    compare_with_genhtmiss_dist(acc, distribution, jobtag, filetag, inputrootfile, logy=True)

    # Compare priors with GEN-level HTmiss we obtain
    comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag, acc_large=acc_large)
    comopare_prior_with_genhtmiss(acc, distribution, jobtag, filetag, logy=True, acc_large=acc_large)

if __name__ == '__main__':
    main()

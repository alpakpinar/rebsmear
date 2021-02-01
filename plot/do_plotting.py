#!/usr/bin/env python

import os
import sys
import re
import argparse
import uproot
import mplhep as hep
from matplotlib import pyplot as plt
from pprint import pprint

pjoin = os.path.join

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='Input ROOT file containing before/after htmiss histograms.')
    parser.add_argument('--dataset_tag', help='Tag for the dataset, default is jetht.', default='jetht')
    args = parser.parse_args()
    return args

def tag_to_plottag(dataset_tag):
    mapping = {
        'jetht' : 'JetHT',
        'qcd' : 'QCD MC',
    }
    return mapping[dataset_tag]

def plot_htmiss_before_and_after(outdir, infile, dataset_tag='jetht'):
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

    ax.text(0., 1., f'{tag_to_plottag(dataset_tag)} 2017',
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
    args = parse_cli()
    # Point the script to the ROOT file containing before/after histograms
    infile = args.infile
    dataset_tag = args.dataset_tag 

    jobtag = re.findall('202\d.*', infile)[0].split('/')[0]


    # Output directory for plotting
    outdir = f'./output/{jobtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    plot_htmiss_before_and_after(outdir, infile=infile, dataset_tag=dataset_tag)

if __name__ == '__main__':
    main()
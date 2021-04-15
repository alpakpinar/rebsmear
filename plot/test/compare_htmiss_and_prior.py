#!/usr/bin/env python

import os
import sys
import re
import uproot
import numpy as np
import mplhep as hep

from matplotlib import pyplot as plt
from coffea import hist
from coffea.util import load
from pprint import pprint

pjoin = os.path.join

def compare_htmiss_and_prior(gen_file, prior_file, prior_ht_bin='500_to_700'):
    '''Plot a comparison of GEN-level HTmiss distribution and priors.'''
    distribution = 'gen_htmiss'
    h_gen = gen_file[distribution].integrate('region', 'inclusive').integrate('dataset')

    h_prior = prior_file[f'gen_htmiss_ht_{prior_ht_bin}']

    # fig, ax = plt.subplots()
    fig, (ax, rax) = plt.subplots(2, 1, figsize=(7,7), gridspec_kw={"height_ratios": (3, 1)}, sharex=True)
    # hep.histplot(h_gen.values()[()], h_gen.axis('htmiss').edges(), ax=ax, label=r'GEN-$H_T^{miss}$', density=True)
    hist.plot1d(h_gen, ax=ax, density=True)
    hep.histplot(h_prior.values, h_prior.edges, ax=ax, label='Prior', density=True)

    handles,labels = ax.get_legend_handles_labels()
    for handle, label  in zip(handles, labels):
        if label == 'None':
            handle.set_label(r'GEN-$H_T^{miss}$')

    ax.legend(handles=handles)
    ax.set_yscale('log')
    ax.set_ylim(1e-6,1e0)
    ax.set_ylabel('Normalized Counts')
    ax.set_xlim(0,300)
    ax.set_xlabel(r'$H_T^{miss} \ (GeV)$')

    lo, _, hi = prior_ht_bin.split('_')

    ax.text(0.,1.,f'${lo} < H_T^{{miss}} < {hi} \\ GeV$',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    ax.text(1.,1.,'QCD MC',
        fontsize=14,
        ha='right',
        va='bottom',
        transform=ax.transAxes
    )
    data_err_opts = {
        'linestyle':'none',
        'marker': '.',
        'markersize': 10.,
        'color':'k',
    }

    xcenters = h_gen.axis('htmiss').centers()
    gen_norm = h_gen.values()[()] / np.sum(h_gen.values()[()])
    ratio = gen_norm / h_prior.values
    rax.plot(xcenters, ratio, **data_err_opts)

    rax.grid(True)
    rax.set_ylim(0.5,1.5)
    rax.set_ylabel('GEN (Norm.) / Prior')
    rax.set_xlabel(r'$H_T^{miss} \ (GeV)$')

    rax.axhline(1., xmin=0, xmax=1, color='red')

    outdir = './output'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'gen_htmiss_vs_prior_ht_{prior_ht_bin}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def main():
    gen_inpath = sys.argv[1]
    if not gen_inpath:
        raise RuntimeError('Provide an input GEN file to extract HTmiss!')
    
    # The file from which we'll extract the GEN-HTmiss distribution
    gen_file = load(gen_inpath)
    # The file where the priors are located
    prior_file = uproot.open('../../input/htmiss_prior.root')

    compare_htmiss_and_prior(gen_file, prior_file)

if __name__ == '__main__':
    main()
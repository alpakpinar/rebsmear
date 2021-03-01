#!/usr/bin/env python

import os
import sys
import uproot
import numpy as np
import mplhep as hep

from matplotlib import pyplot as plt

pjoin = os.path.join

def get_xlabel(distribution):
    mapping = {
        'ak4_phi' : r'All Jet $\phi$',
        'ak4_phi0' : r'Leading Jet $\phi$',
        'ak4_phi1' : r'Trailing Jet $\phi$',
        'ak4_eta' : r'All Jet $\eta$',
        'ak4_eta0' : r'Leading Jet $\eta$',
        'ak4_eta1' : r'Trailing Jet $\eta$',
        'htmiss_bef'  : r'$H_T^{miss} \ (GeV)$ (before reb.)',
        'htmiss_reb'  : r'$H_T^{miss} \ (GeV)$ (after reb.)',
    }

    return mapping[distribution]

def plot_jet_eta_phi(f, distribution):
    h = f[distribution]

    fig, ax = plt.subplots()
    hep.histplot(h.values, h.edges, ax=ax)

    ax.set_yscale('log')
    ax.set_ylim(1e-2,1e4)
    ax.set_xlabel(get_xlabel(distribution))

    delta_htmiss_thresh=80
    ax.text(0., 1., f'$\Delta H_T^{{miss}} < {delta_htmiss_thresh}$ GeV',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outdir = './output/jet_eta_phi'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'{distribution}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def plot_jet_eta_phi_2d(f, distribution):
    h = f[distribution]

    fig, ax = plt.subplots()
    
    xedges, yedges = h.edges
    pc = ax.pcolormesh(xedges, yedges, h.values.T)
    fig.colorbar(pc, ax=ax)
    fig.set_label("Counts")
    
    if distribution == 'ak4_eta_phi0':
        xlabel = r'Leading Jet $\eta$'
        ylabel = r'Leading Jet $\phi$'
    elif distribution == 'ak4_eta_phi1':
        xlabel = r'Trailing Jet $\eta$'
        ylabel = r'Trailing Jet $\phi$'
    elif distribution == 'ak4_eta_phi':
        xlabel = r'All Jet $\eta$'
        ylabel = r'All Jet $\phi$'

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    delta_htmiss_thresh=80
    ax.text(0., 1., f'$\Delta H_T^{{miss}} < {delta_htmiss_thresh}$ GeV',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outdir = './output/jet_eta_phi/2d'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'{distribution}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def main():
    inpath = sys.argv[1]
    f = uproot.open(inpath)

    distributions = ['ak4_phi', 'ak4_phi0', 'ak4_phi1', 'ak4_eta', 'ak4_eta0', 'ak4_eta1', 'htmiss_bef', 'htmiss_reb']

    for distribution in distributions:
        plot_jet_eta_phi(f, distribution=distribution)

    # 2D eta vs. phi distributions
    for distribution in ['ak4_eta_phi', 'ak4_eta_phi0', 'ak4_eta_phi1']:
        plot_jet_eta_phi_2d(f, distribution=distribution)

if __name__ == '__main__':
    main()
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

def plot_jet_eta_phi(f, outtag, distribution, htmiss_thresh=100, plot_norm=True):
    h_lo = f[f'{distribution}_low_final_htmiss']
    h_hi = f[f'{distribution}_high_final_htmiss']

    fig, ax = plt.subplots()
    # Normalize the histograms (if specified)
    if plot_norm:
        lo_values = h_lo.values / np.sum(h_lo.values)
        hi_values = h_hi.values / np.sum(h_hi.values)
    else:
        lo_values = h_lo.values
        hi_values = h_hi.values
    
    hep.histplot(lo_values, h_lo.edges, ax=ax, label=f'$H_T^{{miss}} < {htmiss_thresh} \ GeV$ (final)')
    hep.histplot(hi_values, h_hi.edges, ax=ax, label=f'$H_T^{{miss}} > {htmiss_thresh} \ GeV$ (final)')

    ax.set_yscale('log')
    ax.set_ylim(1e-5,1e1)
    ax.set_xlabel(get_xlabel(distribution))
    ax.set_ylabel('Normalized Counts')
    ax.legend()

    ax.text(0., 1., f'$H_T^{{miss}} > {htmiss_thresh}$ GeV (before reb.)',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'{distribution}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def plot_jet_eta_phi_2d(f, outtag, distribution, htmiss_thresh=100):
    h = f[distribution]

    fig, ax = plt.subplots()
    
    xedges, yedges = h.edges
    pc = ax.pcolormesh(xedges, yedges, h.values.T)
    fig.colorbar(pc, ax=ax)
    fig.set_label("Counts")
    
    if 'ak4_eta_phi0' in distribution:
        xlabel = r'Leading Jet $\eta$'
        ylabel = r'Leading Jet $\phi$'
    elif 'ak4_eta_phi1' in distribution:
        xlabel = r'Trailing Jet $\eta$'
        ylabel = r'Trailing Jet $\phi$'
    else:
        xlabel = r'All Jet $\eta$'
        ylabel = r'All Jet $\phi$'

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    sgn = '<' if 'low_final_htmiss' in distribution else '>'
    ax.text(0., 1., f'$H_T^{{miss}} {sgn} {htmiss_thresh}$ GeV (after reb.)',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outdir = f'./output/{outtag}/2d'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'{distribution}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def main():
    inpath = sys.argv[1]
    f = uproot.open(inpath)

    outtag = inpath.split('/')[-2]

    distributions = ['ak4_phi', 'ak4_phi0', 'ak4_phi1', 'ak4_eta', 'ak4_eta0', 'ak4_eta1']

    for distribution in distributions:
        plot_jet_eta_phi(f, outtag, distribution=distribution)

    # 2D eta vs. phi distributions
    distributions_2d = [
        'ak4_eta_phi_low_final_htmiss',
        'ak4_eta_phi_high_final_htmiss',
        'ak4_eta_phi0_low_final_htmiss',
        'ak4_eta_phi0_high_final_htmiss',
        'ak4_eta_phi1_low_final_htmiss',
        'ak4_eta_phi1_high_final_htmiss',
    ]
    for distribution in distributions_2d:
        plot_jet_eta_phi_2d(f, outtag, distribution=distribution)

if __name__ == '__main__':
    main()
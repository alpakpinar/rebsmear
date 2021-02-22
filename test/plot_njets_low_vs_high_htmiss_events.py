#!/usr/bin/env python

import os
import sys
import re
import uproot
import mplhep as hep

from matplotlib import pyplot as plt

pjoin = os.path.join

def plot_njets(rootfile, outtag, htmiss_thresh=120):
    h_high = rootfile['njets_high_htmiss']
    h_low = rootfile['njets_low_htmiss']
    fig, ax = plt.subplots()
    hep.histplot(h_low.values, h_low.edges, label=f'$H_T^{{miss}}$ < {htmiss_thresh} GeV', density=True)
    hep.histplot(h_high.values, h_high.edges, label=f'$H_T^{{miss}}$ > {htmiss_thresh} GeV', density=True)
    ax.set_xlim(0,11)
    ax.set_xlabel(r'$N_{jet}$')
    ax.set_ylabel(r'% Events')
    ax.legend(title='After rebalancing')

    ax.text(0.,1.,r'$H_T^{miss}$ > 200 GeV (before reb.)',
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

    # Save figure
    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outpath = pjoin(outdir, 'njets.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def main():
    inputrootpath = sys.argv[1]
    f = uproot.open(inputrootpath)

    outtag = inputrootpath.split('/')[1]

    plot_njets(f, outtag)

if __name__ == '__main__':
    main()
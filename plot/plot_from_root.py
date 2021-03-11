#!/usr/bin/env python

import os
import sys
import re
import uproot
import numpy as np
import mplhep as hep

from matplotlib import pyplot as plt
from tqdm import tqdm
from pprint import pprint

pjoin = os.path.join

xlabels = {
    '.*ak4_pt0.*' : r'Leading Jet $p_T$ (GeV)',
    '.*ak4_eta0.*' : r'Leading Jet $\eta$',
    '.*ak4_phi0.*' : r'Leading Jet $\phi$',
    '.*ak4_pt1.*' : r'Trailing Jet $p_T$ (GeV)',
    '.*ak4_eta1.*' : r'Trailing Jet $\eta$',
    '.*ak4_phi1.*' : r'Trailing Jet $\phi$',
    'min_ak4_pt.*' : r'Minimum Jet $p_T$ (GeV)',
    'njets.*' : r'$N_{jet}$',
}

def plot2d(f, outdir):
    # Get the 2D histograms
    distributions = [d for d in f.keys() if '_dhtmiss' in d.decode('utf-8')]

    for distribution in tqdm(distributions):
        h = f[distribution]
        fig, ax = plt.subplots()

        hep.hist2dplot(h.values, h.edges[0], h.edges[1], ax=ax, cbar=False)

        ax.set_ylabel(r'$\Delta H_T^{miss} / H_T^{miss}$')

        for key, label in xlabels.items():
            if re.match(key, distribution.decode('utf-8')):
                xlabel = label
                break

        ax.set_xlabel(xlabel)

        ax.text(0.,1.,'QCD MC',
            fontsize=14,
            ha='left',
            va='bottom',
            transform=ax.transAxes
        )

        outpath = pjoin(outdir, f'{distribution.decode("utf-8").replace(";1", "")}.pdf')
        fig.savefig(outpath)
        plt.close(fig)

def main():
    # Point to "out.root" file containing histograms
    inpath = sys.argv[1]
    f = uproot.open(inpath)

    outdir = os.path.dirname(inpath)

    plot2d(f, outdir)

if __name__ == '__main__':
    main()
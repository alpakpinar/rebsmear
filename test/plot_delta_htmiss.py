#!/usr/bin/env python

import os
import sys
import re
import uproot
import numpy as np
import ROOT as r

from matplotlib import pyplot as plt
from glob import glob

pjoin = os.path.join

def plot_delta_htmiss(infiles, outtag, htmiss_thresh=150):
    difflist = []
    for inpath in infiles:
        f = r.TFile(inpath, 'READ')

        keys = f.GetListOfKeys()
        
        events_bef = [key.GetName() for key in keys if key.GetName().startswith('before')]
        events_reb = [key.GetName() for key in keys if key.GetName().startswith('rebalanced')]
        assert(len(events_bef) == len(events_reb))
        nevents = len(events_bef)

        print(f'Reading from file: {inpath}')
        print(f'Number of events: {nevents}')

        for idx in range(nevents):
            print(f'{idx}/{nevents}', end='\r')
            ws_bef = f.Get(events_bef[idx])
            ws_reb = f.Get(events_reb[idx])

            htmiss_bef = ws_bef.function('gen_htmiss_pt').getValV()
            htmiss_reb = ws_reb.function('gen_htmiss_pt').getValV()

            # Threshold on HTmiss before rebalancing
            if htmiss_bef < htmiss_thresh:
                continue

            # Calculate the HTmiss diff
            diff = htmiss_bef - htmiss_reb

            difflist.append(diff)

    # Plot the distribution from all files
    htbins = np.arange(10,310,10)

    fig, ax = plt.subplots()
    ax.hist(difflist, bins=htbins)

    ax.set_xlabel(r'$\Delta H_T^{miss}$ (GeV)')

    ax.text(0., 1., f'$H_T^{{miss}} > {htmiss_thresh} \\ GeV$ (before reb.)',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    ax.text(1., 1., 'QCD MC',
        fontsize=14,
        ha='right',
        va='bottom',
        transform=ax.transAxes
    )

    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, f'deltahtmiss_thresh_{htmiss_thresh}.pdf')
    fig.savefig(outpath)
    plt.close(fig)

    print(f'File saved: {outpath}')

def main():
    inpath = sys.argv[1]

    outtag = inpath.split('/')[-2]

    infiles = glob(pjoin(inpath, 'ws_eventchunk*.root'))

    for thresh in [150]:
        plot_delta_htmiss(infiles, outtag, htmiss_thresh=thresh)

if __name__ == '__main__':
    main()
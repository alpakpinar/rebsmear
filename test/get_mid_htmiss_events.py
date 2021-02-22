#!/usr/bin/env python

import os
import sys
import re

import numpy as np
import ROOT as r
import uproot
from glob import glob

pjoin = os.path.join

def htmiss_func_name():
    return 'gen_htmiss_pt'

def ht_func_name():
    return 'gen_ht'

def save_mid_htmiss_events(infiles, outtag, htmiss_low=50, htmiss_high=150):
    njets_list = []
    htmiss_after_list = []

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
            # Get the events from the workspace
            event_bef = f.Get(events_bef[idx])
            event_reb = f.Get(events_reb[idx])

            # Get HTmiss after rebalancing, if it is not larger than
            # the threshold we specify, continue
            htmiss_bef = event_bef.function( htmiss_func_name() ).getValV()
            htmiss_reb = event_reb.function( htmiss_func_name() ).getValV()
            
            ht_bef = event_bef.function( ht_func_name() ).getValV()
            ht_reb = event_reb.function( ht_func_name() ).getValV()

            # Jet information
            njets = int(event_bef.var('njets').getValV())

            # Here, only considering events at mid-HTmiss range, say 50 < HTmiss < 150 GeV
            event_filter = (htmiss_bef > htmiss_low) & (htmiss_bef < htmiss_high)
            if not event_filter:
                continue

            njets_list.append(njets)
            htmiss_after_list.append(htmiss_reb)

    # After we're done with all files, make histograms and save to a ROOT file
    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outputrootpath = pjoin(outdir, 'mid_htmiss_events.root')
    outputrootfile = uproot.recreate(outputrootpath)

    njetsbins = np.arange(0.5,10.5)
    h_njets, edges = np.histogram(njets_list, bins=njetsbins)
    outputrootfile['njets'] = (h_njets, edges)
    h_htmiss, edges = np.histogram(htmiss_after_list)
    outputrootfile['htmiss'] = (h_htmiss, edges)

    print(f'Histograms saved to ROOT file: {outputrootpath}')

def main():
    # Input workspace file
    inpath = sys.argv[1]
    outtag = re.findall('202\d.*', inpath)[0].replace('/','')
    infiles = glob(pjoin(inpath, 'ws_eventchunk*.root'))

    save_mid_htmiss_events(infiles, outtag)

if __name__ == '__main__':
    main()
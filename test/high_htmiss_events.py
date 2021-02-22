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

def dump_high_htmiss_events(infiles, outtag, htmiss_thresh=200):
    njets_highht_list = []
    njets_lowht_list = []
    njetsbins = np.arange(0.5,10.5)

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

            # Two categories of events here:
            # 1. Events starting from high HTmiss, but pushed towards very low HTmiss
            # 2. Events starting from high HTmiss, but still at the tail after the fit
            if (htmiss_reb > 120) & (htmiss_bef > htmiss_thresh):
                njets_highht_list.append(njets)
            elif (htmiss_reb < 120) & (htmiss_bef > htmiss_thresh):
                njets_lowht_list.append(njets)

    # Njets histogram: Save to output ROOT file
    h_high, edges = np.histogram(njets_highht_list, bins=njetsbins)
    h_low, edges = np.histogram(njets_lowht_list, bins=njetsbins)
    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, 'njets.root')
    outputrootfile = uproot.recreate(outpath)
    outputrootfile['njets_high_htmiss'] = (h_high, edges) 
    outputrootfile['njets_low_htmiss'] = (h_low, edges)

    print(f'ROOT file saved: {outpath}') 

def main():
    # Input workspace file
    inpath = sys.argv[1]

    outtag = re.findall('202\d.*', inpath)[0].replace('/','')

    infiles = glob(pjoin(inpath, 'ws_eventchunk*.root'))

    dump_high_htmiss_events(infiles, outtag)

if __name__ == '__main__':
    main()
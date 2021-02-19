#!/usr/bin/env python

import os
import sys
import ROOT as r

pjoin = os.path.join

def htmiss_func_name():
    return 'gen_htmiss_pt'

def ht_func_name():
    return 'gen_ht'

def dump_high_htmiss_events(f, htmiss_thresh=200):
    keys = f.GetListOfKeys()
    events_bef = [key.GetName() for key in keys if key.GetName().startswith('before')]
    events_reb = [key.GetName() for key in keys if key.GetName().startswith('rebalanced')]
    assert(len(events_bef) == len(events_reb))
    nevents = len(events_bef)

    print(f'Processing file, number of events:  {nevents}')
    print('='*20)

    num_events_with_highhtmiss = 0

    for idx in range(nevents):
        print(f'{idx}/{nevents}', end='\r')
        # Get the events from the workspace
        event_bef = f.Get(events_bef[idx])
        event_reb = f.Get(events_reb[idx])

        # Get HTmiss after rebalancing, if it is not larger than
        # the threshold we specify, continue
        htmiss_reb = event_reb.function( htmiss_func_name() ).getValV()
        if htmiss_reb < htmiss_thresh:
            continue

        htmiss_bef = event_bef.function( htmiss_func_name() ).getValV()
        ht_bef = event_bef.function( ht_func_name() ).getValV()
        ht_reb = event_reb.function( ht_func_name() ).getValV()

        print(f'HTmiss before: {htmiss_bef:.3f}')
        print(f'HTmiss after: {htmiss_reb:.3f}')
        print(f'HT before: {ht_bef:.3f}')
        print(f'HT after: {ht_reb:.3f}')
        print('*'*20)

        num_events_with_highhtmiss += 1

    print('\n')
    print('DONE')
    print(f'Events with high HTmiss: {num_events_with_highhtmiss} / {nevents}')

def main():
    # Input workspace file
    inpath = sys.argv[1]
    f = r.TFile(inpath, 'READ')

    dump_high_htmiss_events(f)

if __name__ == '__main__':
    main()
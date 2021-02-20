#!/usr/bin/env python

import os
import sys
import ROOT as r

pjoin = os.path.join

def htmiss_func_name():
    return 'gen_htmiss_pt'

def ht_func_name():
    return 'gen_ht'

def dump_high_htmiss_events(inpath, htmiss_thresh=200):
    f = r.TFile(inpath, 'READ')

    keys = f.GetListOfKeys()
    events_bef = [key.GetName() for key in keys if key.GetName().startswith('before')]
    events_reb = [key.GetName() for key in keys if key.GetName().startswith('rebalanced')]
    assert(len(events_bef) == len(events_reb))
    nevents = len(events_bef)

    print(f'Processing file, number of events:  {nevents}')

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

        # Jet information
        njets = int(event_bef.var('njets').getValV())
        # Get jet pt and phi
        jet_pt_before, jet_pt_after = [], []
        jet_phi = []
        f.cd()
        for ijet in range(njets):
            ptname = 'reco_pt_' + str(ijet)
            ptname_after = 'gen_pt_' + str(ijet)
            phiname = 'reco_phi_' + str(ijet)

            pt_before = event_bef.var(ptname).getValV()
            pt_after = event_reb.var(ptname_after).getValV()
            phi = event_bef.var(phiname).getValV()

            jet_pt_before.append(pt_before)
            jet_pt_after.append(pt_after)
            jet_phi.append(phi)

        print('='*20)
        print(f'Number of jets: {njets}')
        for idx in range(len(jet_phi)):
            print('-'*20)
            print(f'Jet {idx}')
            print(f'Jet pt before: {jet_pt_before[idx]:.3f}')
            print(f'Jet pt after: {jet_pt_after[idx]:.3f}')
            print(f'Jet phi: {jet_phi[idx]:.3f}')

        print('-'*20)

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

    dump_high_htmiss_events(inpath)

if __name__ == '__main__':
    main()
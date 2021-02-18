#!/usr/bin/env python

import os
import sys
import ROOT as r

pjoin = os.path.join

def dump_htmiss_before_and_after(f, logf, nentries=50):
    events_before = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('before')]    
    events_after = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('rebalanced')]    

    logf.write('HTmiss before and after:\n')
    logf.write(f'Running on {nentries} events:\n\n')
    for idx in range(nentries):
        ws_bef = f.Get(events_before[idx])
        ws_aft = f.Get(events_after[idx])

        ht_bef = ws_bef.function('gen_ht').getValV()

        htmiss_bef = ws_bef.function('gen_htmiss_pt').getValV()
        htmiss_aft = ws_aft.function('gen_htmiss_pt').getValV()

        logf.write(f'HT before: {ht_bef:.3f}\n')
        logf.write(f'HTmiss before: {htmiss_bef:.3f}\n')
        logf.write(f'HTmiss after: {htmiss_aft:.3f}\n')
        logf.write('*'*20 + '\n')

def main():
    inputrootfile = sys.argv[1]
    f = r.TFile(inputrootfile, 'READ')

    # Log file to save output
    logdir = './output'
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logfile = pjoin(logdir, 'log.txt')

    nentries=50
    with open(logfile, 'w+') as logf:
        logf.write('HTmiss before and after:\n')
        logf.write(f'Input ROOT file: {inputrootfile}\n')
        logf.write(f'Running on {nentries} events:\n\n')

        dump_htmiss_before_and_after(f, logf, nentries)

    print(f'Log file saved: {logfile}')

if __name__ == '__main__':
    main()
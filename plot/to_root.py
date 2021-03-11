#!/usr/bin/env python

import os
import sys
import re
import uproot
import numpy as np
import ROOT as r

from tqdm import tqdm
from glob import glob

pjoin = os.path.join

def dump_to_root(infiles, outf, histos):
    for inpath in tqdm(infiles):
        f = r.TFile(inpath, 'READ')
        events_before = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('before')] 
        events_after = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('rebalanced')]

        assert len(events_before) == len(events_after)
        nevents = len(events_before)

        for idx in range(nevents):
            ws_bef = f.Get(events_before[idx])
            ws_reb = f.Get(events_after[idx])

            htmiss_bef = ws_bef.function('gen_htmiss_pt').getValV()
            htmiss_reb = ws_reb.function('gen_htmiss_pt').getValV()

            njets = int(ws_bef.var('njets').getValV())

            dhtmiss = np.abs(htmiss_bef - htmiss_reb) / htmiss_bef

            jet_pt_list = []

            for ijet in range(njets):
                jet_phi = ws_bef.var('reco_phi_'+str(ijet)).getValV()
                jet_eta = ws_bef.var('reco_eta_'+str(ijet)).getValV()
                jet_pt = ws_bef.var('reco_pt_'+str(ijet)).getValV()

                jet_pt_list.append(jet_pt)

                if ijet == 0:
                    histos['ak4_pt0_dhtmiss'].Fill(jet_pt, dhtmiss)
                    histos['ak4_eta0_dhtmiss'].Fill(jet_eta, dhtmiss)
                    histos['ak4_phi0_dhtmiss'].Fill(jet_phi, dhtmiss)
                elif ijet == 1:
                    histos['ak4_pt1_dhtmiss'].Fill(jet_pt, dhtmiss)
                    histos['ak4_eta1_dhtmiss'].Fill(jet_eta, dhtmiss)
                    histos['ak4_phi1_dhtmiss'].Fill(jet_phi, dhtmiss)

            histos['dhtmiss'].Fill(dhtmiss)

            histos['min_ak4_pt_dhtmiss'].Fill(min(jet_pt_list), dhtmiss)
            histos['njets_dhtmiss'].Fill(njets, dhtmiss)

    outf.cd()
    outf.Write()

def setup_histos():
    histos = {}
    histos['ak4_pt0_dhtmiss'] = r.TH2F('ak4_pt0_dhtmiss', 'ak4_pt0_dhtmiss', 20, 0, 800, 20, 0, 1)
    histos['ak4_eta0_dhtmiss'] = r.TH2F('ak4_eta0_dhtmiss', 'ak4_eta0_dhtmiss', 20, -5, 5, 20, 0, 1)
    histos['ak4_phi0_dhtmiss'] = r.TH2F('ak4_phi0_dhtmiss', 'ak4_phi0_dhtmiss', 20, -np.pi, np.pi, 20, 0, 1)

    histos['ak4_pt1_dhtmiss'] = r.TH2F('ak4_pt1_dhtmiss', 'ak4_pt1_dhtmiss', 20, 0, 800, 20, 0, 1)
    histos['ak4_eta1_dhtmiss'] = r.TH2F('ak4_eta1_dhtmiss', 'ak4_eta1_dhtmiss', 20, -5, 5, 20, 0, 1)
    histos['ak4_phi1_dhtmiss'] = r.TH2F('ak4_phi1_dhtmiss', 'ak4_phi1_dhtmiss', 20, -np.pi, np.pi, 20, 0, 1)

    histos['dhtmiss'] = r.TH1F('dhtmiss', 'dhtmiss', 50, 0, 1)
    histos['min_ak4_pt_dhtmiss'] = r.TH2F('min_ak4_pt_dhtmiss', 'min_ak4_pt_dhtmiss', 15, 0, 300, 20, 0, 1)
    histos['njets_dhtmiss'] = r.TH2F('njets_dhtmiss', 'njets_dhtmiss', 10, 0, 10, 20, 0, 1)

    return histos

def main():
    # Input directory containing workspace files
    inpath = sys.argv[1]

    infiles = glob( pjoin(inpath, 'ws*.root') )

    outtag = re.findall('202\d.*', inpath)[0].replace('/', '')

    # Output ROOT file
    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = pjoin(outdir, 'out.root')
    outf = r.TFile(outpath, 'RECREATE')

    histos = setup_histos()

    dump_to_root(infiles, outf, histos)    

if __name__ == '__main__':
    main()
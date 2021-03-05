#!/usr/bin/env python

import os
import sys
import re
import uproot
import ROOT as r
import numpy as np
from glob import glob
from tqdm import tqdm

pjoin = os.path.join


h_jet_eta_phi = r.TH2F('ak4_eta_phi', r'Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi)
h_jet_eta_phi0 = r.TH2F('ak4_eta_phi0', r'Leading jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi)
h_jet_eta_phi1 = r.TH2F('ak4_eta_phi1', r'Trailing jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi)

h_htmiss_bef = r.TH1F('htmiss_bef', r'H_T^{miss}', 50, 0, 500)
h_htmiss_reb = r.TH1F('htmiss_reb', r'H_T^{miss}', 50, 0, 500)

def plot_jet_kinematics(infiles, outtag, outf, histos, htmiss_thresh=100):
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

            # Take events statring with relatively high HTmiss
            if htmiss_bef < htmiss_thresh:
                continue

            if htmiss_reb < htmiss_thresh:
                htype = 'low_final_htmiss'
            else:
                htype = 'high_final_htmiss'

            njets = int(ws_bef.var('njets').getValV())

            # Get jet kinematic values
            for ijet in range(njets):
                jet_phi = ws_bef.var('reco_phi_'+str(ijet)).getValV()
                jet_eta = ws_bef.var('reco_eta_'+str(ijet)).getValV()

                # Leading jet
                if ijet == 0:
                    histos['jet_phi0'][htype].Fill(jet_phi)
                    histos['jet_eta0'][htype].Fill(jet_eta)

                    histos['jet_eta_phi0'][htype].Fill(jet_eta, jet_phi)
                    
                # Trailing jet
                elif ijet == 1:
                    histos['jet_phi1'][htype].Fill(jet_phi)
                    histos['jet_eta1'][htype].Fill(jet_eta)

                    histos['jet_eta_phi1'][htype].Fill(jet_eta, jet_phi)

                # All jets
                histos['jet_eta'][htype].Fill(jet_eta)
                histos['jet_phi'][htype].Fill(jet_phi)
                histos['jet_eta_phi'][htype].Fill(jet_eta, jet_phi)

                # h_htmiss_bef.Fill(htmiss_bef)
                # h_htmiss_reb.Fill(htmiss_reb)

    outf.cd()
    outf.Write()

def main():
    # Input directory containing workspace files
    inpath = sys.argv[1]

    infiles = glob( pjoin(inpath, 'ws*.root') )

    outtag = re.findall('202\d.*', inpath)[0].replace('/', '')

    # Output ROOT file
    outdir = f'./output/{outtag}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outf = r.TFile(pjoin(outdir, 'jet_eta_phi.root'), 'RECREATE')

    # Histograms to be filled: For low and high delta HTmiss
    histos = {
        'jet_phi' : {
            'low_final_htmiss' : r.TH1F('ak4_phi_low_final_htmiss', r'Jet $\phi$', 50, -np.pi, np.pi),
            'high_final_htmiss' : r.TH1F('ak4_phi_high_final_htmiss', r'Jet $\phi$', 50, -np.pi, np.pi),
        },
        'jet_phi0' : {
            'low_final_htmiss' : r.TH1F('ak4_phi0_low_final_htmiss', r'Leading Jet $\phi$', 50, -np.pi, np.pi),
            'high_final_htmiss' : r.TH1F('ak4_phi0_high_final_htmiss', r'Leading Jet $\phi$', 50, -np.pi, np.pi),
        },
        'jet_phi1' : {
            'low_final_htmiss' : r.TH1F('ak4_phi1_low_final_htmiss', r'Trailing Jet $\phi$', 50, -np.pi, np.pi),
            'high_final_htmiss' : r.TH1F('ak4_phi1_high_final_htmiss', r'Trailing Jet $\phi$', 50, -np.pi, np.pi),
        },
        'jet_eta' : {
            'low_final_htmiss' : r.TH1F('ak4_eta_low_final_htmiss', r'Jet $\eta$', 50, -5, 5),
            'high_final_htmiss' : r.TH1F('ak4_eta_high_final_htmiss', r'Jet $\eta$', 50, -5, 5),
        },
        'jet_eta0' : {
            'low_final_htmiss' : r.TH1F('ak4_eta0_low_final_htmiss', r'Leading Jet $\eta$', 50, -5, 5),
            'high_final_htmiss' : r.TH1F('ak4_eta0_high_final_htmiss', r'Leading Jet $\eta$', 50, -5, 5),
        },
        'jet_eta1' : {
            'low_final_htmiss' : r.TH1F('ak4_eta1_low_final_htmiss', r'Trailing Jet $\eta$', 50, -5, 5),
            'high_final_htmiss' : r.TH1F('ak4_eta1_high_final_htmiss', r'Trailing Jet $\eta$', 50, -5, 5),
        },
        'jet_eta_phi' : {
            'low_final_htmiss' : r.TH2F('ak4_eta_phi_low_final_htmiss', r'Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
            'high_final_htmiss' : r.TH2F('ak4_eta_phi_high_final_htmiss', r'Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
        },
        'jet_eta_phi0' : {
            'low_final_htmiss' : r.TH2F('ak4_eta_phi0_low_final_htmiss', r'Leading Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
            'high_final_htmiss' : r.TH2F('ak4_eta_phi0_high_final_htmiss', r'Leading Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
        },
        'jet_eta_phi1' : {
            'low_final_htmiss' : r.TH2F('ak4_eta_phi1_low_final_htmiss', r'Trailing Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
            'high_final_htmiss' : r.TH2F('ak4_eta_phi1_high_final_htmiss', r'Trailing Jet $\eta$-$\phi$', 25, -5, 5, 10, -np.pi, np.pi),
        },
    }

    plot_jet_kinematics(infiles, outtag, outf, histos)

if __name__ == '__main__':
    main()

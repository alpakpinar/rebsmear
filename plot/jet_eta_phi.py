#!/usr/bin/env python

import os
import sys
import uproot
import ROOT as r
import numpy as np

pjoin = os.path.join

# Output ROOT file
outf = r.TFile('jet_eta_phi.root', 'RECREATE')

h_jet_phi = r.TH1F('ak4_phi', r'Jet $\phi$', 50, -np.pi, np.pi)
h_jet_phi0 = r.TH1F('ak4_phi0', r'Leading Jet $\phi$', 50, -np.pi, np.pi)
h_jet_phi1 = r.TH1F('ak4_phi1', r'Trailing Jet $\phi$', 50, -np.pi, np.pi)
h_jet_eta = r.TH1F('ak4_eta', r'Jet $\eta$', 50, 0, 5)
h_jet_eta0 = r.TH1F('ak4_eta0', r'Leading jet $\eta$', 50, 0, 5)
h_jet_eta1 = r.TH1F('ak4_eta1', r'Trailing jet $\eta$', 50, 0, 5)

h_htmiss_bef = r.TH1F('htmiss_bef', r'H_T^{miss}', 50, 0, 500)
h_htmiss_reb = r.TH1F('htmiss_reb', r'H_T^{miss}', 50, 0, 500)

def plot_jet_kinematics(inpath, htmiss_bef_thresh=120, deltahtmiss_thresh=80):
    f = r.TFile(inpath, 'READ')
    events_before = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('before')] 
    events_after = [key.GetName() for key in f.GetListOfKeys() if key.GetName().startswith('rebalanced')]

    assert len(events_before) == len(events_after)
    nevents = len(events_before)

    for idx in range(nevents):
        print(f'Running: {idx}/{nevents}', end='\r')
        ws_bef = f.Get(events_before[idx])
        ws_reb = f.Get(events_after[idx])

        htmiss_bef = ws_bef.function('gen_htmiss_pt').getValV()
        htmiss_reb = ws_reb.function('gen_htmiss_pt').getValV()

        # Take events statring with relatively high HTmiss
        if htmiss_bef < htmiss_bef_thresh:
            continue

        delta_htmiss = np.abs(htmiss_bef - htmiss_reb)
        if delta_htmiss > deltahtmiss_thresh:
            continue

        njets = int(ws_bef.var('njets').getValV())

        # Get jet kinematic values
        for ijet in range(njets):
            jet_phi = ws_bef.var('reco_phi_'+str(ijet)).getValV()
            jet_eta = ws_bef.var('reco_eta_'+str(ijet)).getValV()

            # Leading jet
            if ijet == 0:
                h_jet_phi0.Fill(jet_phi)
                h_jet_eta0.Fill(jet_eta)
                
            # Trailing jet
            elif ijet == 1:
                h_jet_phi1.Fill(jet_phi)
                h_jet_eta1.Fill(jet_eta)

            h_jet_phi.Fill(jet_phi)
            h_jet_eta.Fill(jet_eta)

            h_htmiss_bef.Fill(htmiss_bef)
            h_htmiss_reb.Fill(htmiss_reb)

    outf.cd()
    outf.Write()

def main():
    # Input workspace file
    inpath = sys.argv[1]

    plot_jet_kinematics(inpath)

if __name__ == '__main__':
    main()

import time
import numpy as np
from numpy.lib.function_base import extract
import ROOT as r
r.gSystem.Load('libRooFit')
from rebalance import Jet, RebalanceWSFactory
import uproot
from matplotlib import pyplot as plt


def read_jets(event):
    f = uproot.open("input/tree_22.root")
    t = f['Events']
    n = event
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])
    
    return [Jet(pt=ipt, phi=iphi, eta=ieta) for ipt, iphi, ieta in zip(pt, phi, eta)]


def extract_values(ws, tier):
    x, y = [], []
    htx, hty = [], []

    for i in range(int(ws.var("njets").getValV())):
        x.append(ws.var(f"{tier}_px_{i}").getValV())
        y.append(ws.var(f"{tier}_py_{i}").getValV())

    htx = -np.sum(x)
    hty = -np.sum(y)

    return x, y, htx, hty

def extract_values_pt_phi(ws, tier):
    pt,phi = [], []
    htx, hty = [], []

    for i in range(int(ws.var("njets").getValV())):
        pt.append(ws.var(f"{tier}_pt_{i}").getValV())
        phi.append(ws.var(f"{tier}_phi_{i}").getValV())

    pt = np.array(pt)
    phi = np.array(phi)
    x = pt * np.cos(phi)
    y = pt * np.sin(phi)
    htmiss_x = -np.sum(x)
    htmiss_y = -np.sum(y)

    ht = np.sum(pt)

    return x, y, htmiss_x, htmiss_y, ht

def plot_plane(ws, tag):
    plt.gcf().clf()
    fig = plt.gcf()
    ax = plt.gca()
    
    # Reco
    reco_x, reco_y, reco_htmissx, reco_htmissy, reco_ht = extract_values_pt_phi(ws, "reco")
    gen_x, gen_y, gen_htmissx, gen_htmissy, gen_ht = extract_values_pt_phi(ws, "gen")



    for i in range(len(reco_x)):
        arr_reco_jet = ax.arrow(
                x=0,
                y=0,
                dx=reco_x[i],
                dy=reco_y[i],
                head_width=10,
                color='navy',
                # label='Reco jet' if i==0 else None
                )
        arr_gen_jet = ax.arrow(   
                 x=0,
                 y=0,
                 dx=gen_x[i],
                 dy=gen_y[i],
                 head_width=10,
                 color='crimson',
                #  label='Gen jet' if i==0 else None
                 )
    
    reco_htmiss = np.hypot(reco_htmissx, reco_htmissy)
    gen_htmiss = np.hypot(gen_htmissx, gen_htmissy)
    arr_reco_ht = ax.arrow(
             x=0,
             y=0,
             dx=reco_htmissx,
             dy=reco_htmissy,
             head_width=10,
             color='navy',
             width=10,
             alpha=0.5,
            #  fill=False,
             label=f'Reco $H_{{T}}^{{miss}}$ ({reco_htmiss:.0f} GeV)')
    arr_gen_ht = ax.arrow(
             x=0,
             y=0,
             dx=gen_htmissx,
             dy=gen_htmissy,
             head_width=10,
             color='crimson',
             width=10,
             alpha=0.5,
            #  fill=False,
             label=f'Gen $H_{{T}}^{{miss}}$ ({gen_htmiss:.0f} GeV)')

    axis_maximum = 1.2*max([abs(x) for x in (reco_x + reco_y + [reco_htmiss])])
    ax.set_ylim(-axis_maximum, axis_maximum)
    ax.set_xlim(-axis_maximum, axis_maximum)
    ax.set_title(f"{tag}, NLL = {ws.function('nll').getValV():.2f}")
    ax.legend([arr_reco_jet, arr_gen_jet, arr_reco_ht, arr_gen_ht], ['RECO jet', 'GEN jet', f'RECO $H_{{T}}^{{miss}}$ ({reco_htmiss:.0f} GeV)', f'GEN $H_{{T}}^{{miss}}$ ({gen_htmiss:.0f} GeV)'])

    ax.set_xlabel(r'$p_x \ (GeV)$')
    ax.set_ylabel(r'$p_y \ (GeV)$')

    ax.text(0.98, 0.1, f'$H_T^{{reco}} = {reco_ht:.2f}$ GeV',
        fontsize=12,
        ha='right',
        va='top',
        transform=ax.transAxes
    )

    fig.savefig(f"output/test_{tag}.png", dpi=300)


def main():
    # Record the running time
    starttime = time.time()

    # Number of events to run over
    num_events = 10

    f=r.TFile(f"./output/ws_all.root","RECREATE")

    for event in range(num_events):
        jets = read_jets(event)
        rbwsfac = RebalanceWSFactory(jets)
        rbwsfac.set_jer_source("./input/jer.root","jer_data")
        rbwsfac.build()
        ws = rbwsfac.get_ws()
        ws.Print("v")

        # for i in range(int(ws.var("njets").getValV())):
        #     print(i, jets[i].px, ws.var(f"gen_px_{i}").getValV(), ws.var(f"reco_px_{i}").getValV())
        
        # for i in range(int(ws.var("njets").getValV())):
        #     print(i, jets[i].py, ws.var(f"gen_py_{i}").getValV(), ws.var(f"reco_py_{i}").getValV())


        plot_plane(ws, tag=f"{event}_before")
        # ws.Write('before')
        m = r.RooMinimizer(ws.function("nll"))
        m.migrad()
        f.cd()
        ws.Write(f'rebalanced_event_{event}')
        plot_plane(ws, tag=f"{event}_after")

    print('*'*20)
    print('JOB INFO:')
    endtime = time.time()
    timeinterval = endtime - starttime
    timeinterval_per_event = (endtime - starttime) / num_events
    print(f'Ran over {num_events} events')
    print(f'Total running time: {timeinterval:.3f} s')
    print(f'Running time/event: {timeinterval_per_event:.3f} s')
    print('*'*20)

    return ws
if __name__ == "__main__":
    ws = main()
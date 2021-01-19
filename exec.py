import numpy as np
from numpy.lib.function_base import extract
import ROOT as r
r.gSystem.Load('libRooFit')
from rebalance import Jet, RebalanceWSFactory
import uproot
from matplotlib import pyplot as plt


def read_jets(event):
    f = uproot.open("tree_22.root")
    t = f['Events']
    n = event
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])
    
    return [Jet(ipt, iphi, ieta) for ipt, iphi, ieta in zip(pt, phi, eta)]


def extract_values(ws, tier):
    x, y = [], []
    htx, hty = [], []

    for i in range(int(ws.var("njets").getValV())):
        x.append(ws.var(f"{tier}_px_{i}").getValV())
        y.append(ws.var(f"{tier}_py_{i}").getValV())

    htx = -np.sum(x)
    hty = -np.sum(y)

    return x, y, htx, hty

def plot_plane(ws, tag):
    plt.gcf().clf()
    fig = plt.gcf()
    ax = plt.gca()
    
    # Reco
    reco_x, reco_y, reco_htx, reco_hty = extract_values(ws, "reco")
    gen_x, gen_y, gen_htx, gen_hty = extract_values(ws, "gen")

    for i in range(len(reco_x)):
        ax.arrow(
                x=0,
                y=0,
                dx=reco_x[i],
                dy=reco_y[i],
                head_width=10,
                color='navy',
                label='Reco jet' if i==0 else None
                )
        ax.arrow(   
                 x=0,
                 y=0,
                 dx=gen_x[i],
                 dy=gen_y[i],
                 head_width=10,
                 color='crimson',
                 label='Gen jet' if i==0 else None
                 )
    
    reco_ht = np.hypot(reco_htx, reco_hty)
    gen_ht = np.hypot(gen_htx, gen_hty)
    ax.arrow(
             x=0,
             y=0,
             dx=reco_htx,
             dy=reco_hty,
             head_width=10,
             color='navy',
             width=5,
             alpha=0.5,
             fill=False,
             label=f'Reco $H_{{T}}^{{miss}}$ ({reco_ht:.0f} GeV)')
    ax.arrow(
             x=0,
             y=0,
             dx=gen_htx,
             dy=gen_hty,
             head_width=10,
             color='crimson',
             width=5,
             fill=False,
             label=f'Gen $H_{{T}}^{{miss}}$ ({gen_ht:.0f} GeV)')


    axis_maximum = 1.2*max([abs(x) for x in (reco_x + reco_y + [reco_ht])])
    ax.set_ylim(-axis_maximum, axis_maximum)
    ax.set_xlim(-axis_maximum, axis_maximum)
    ax.set_title(f"{tag}, NLL = {ws.function('nll').getValV():.2f}")
    ax.legend()
    fig.savefig(f"output/test_{tag}.png", dpi=300)


def main():

    for event in range(10):
        jets = read_jets(event)
        rbwsfac = RebalanceWSFactory(jets)
        rbwsfac.build()
        ws = rbwsfac.get_ws()
        # ws.Print("v")

        # for i in range(int(ws.var("njets").getValV())):
        #     print(i, jets[i].px, ws.var(f"gen_px_{i}").getValV(), ws.var(f"reco_px_{i}").getValV())
        
        # for i in range(int(ws.var("njets").getValV())):
        #     print(i, jets[i].py, ws.var(f"gen_py_{i}").getValV(), ws.var(f"reco_py_{i}").getValV())



        plot_plane(ws, tag=f"{event}_before")
        m = r.RooMinimizer(ws.function("nll"))
        m.migrad()
        plot_plane(ws, tag=f"{event}_after")

if __name__ == "__main__":
    main()
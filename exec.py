from rebalance import Jet, RebalanceWSFactory
import uproot



def read_jets():
    f = uproot.open("tree_22.root")
    t = f['Events']
    n = 5
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])
    
    return [Jet(ipt, iphi, ieta) for ipt, iphi, ieta in zip(pt, phi, eta)]


jets = read_jets()

rbwsfac = RebalanceWSFactory(jets)
rbwsfac.build()
ws = rbwsfac.get_ws()
ws.Print("v")
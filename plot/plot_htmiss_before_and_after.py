#!/usr/bin/env python

import os
import sys
import re
import glob
import uproot
import ROOT as r
import mplhep as hep
import matplotlib.colors as colors
from matplotlib import pyplot as plt
from coffea.util import load
from coffea import hist
from pprint import pprint

pjoin = os.path.join

def htmiss_func_name():
    return 'gen_htmiss_pt'

def tag_to_plottag(dataset_tag):
    mapping = {
        'jetht' : 'JetHT',
        'qcd' : 'QCD MC',
    }
    return mapping[dataset_tag]

def save_htmiss_before_and_after(infiles, outdir):
    '''Save the HTmiss histograms before and after rebalancing, using the list of provided input files.'''
    # Initialize two ROOT histograms (before/after)
    h_bef = r.TH1F('htmiss_before', r'$H_T^{miss} \ (GeV)$', 50, 0, 500)
    h_aft = r.TH1F('htmiss_after', r'$H_T^{miss} \ (GeV)$', 50, 0, 500)

    for infile in infiles:
        print(f'Reading events from file: {infile}')
        f = r.TFile(infile)

        keys = f.GetListOfKeys()
        nkeys = len(keys)

        for idx in range(nkeys):
            totalnumkeys = nkeys-1
            if idx % 100 == 0 and idx > 0:
                print(f'Reading entry: {idx}/{totalnumkeys} ({idx / totalnumkeys * 100:.2f}%)', end='\r')
            
            name = keys[idx].GetName()
            if name.startswith('ProcessID'):
                continue

            ws = f.Get(name)
            # Extract the HTmiss value  out of the workspace
            htmiss = ws.function(htmiss_func_name()).getValV()

            if name.startswith('before'):
                h_bef.Fill(htmiss)
            elif name.startswith('rebalanced'):
                h_aft.Fill(htmiss)

    # Once we're done filling the histogram with all the events, save the two histograms to a new ROOT file
    outpath = pjoin(outdir, 'htmiss_after_reb.root')
    outf = r.TFile(outpath, 'RECREATE')

    outf.cd()
    h_bef.Write()
    h_aft.Write()

    print(f'Histograms saved to: {outpath}')
    return outpath

def save_htmiss_before_and_after_2d(infiles, outdir):
    '''Plot 2D HTmiss histogram, specifying HTmiss in events before and after rebalancing.'''
    h = r.TH2F('htmiss_2d_before_after', r'$H_T^{miss} \ (GeV)$', 50, 0, 500, 50, 0, 500)

    for infile in infiles:
        print(f'Reading events from file: {infile}')
        f = r.TFile(infile)

        keys = f.GetListOfKeys()

        events_before = [e.GetName() for e in keys if e.GetName().startswith('before')]
        events_after = [e.GetName() for e in keys if e.GetName().startswith('rebalanced')]
        assert(len(events_before) == len(events_after))
        nevents = len(events_before)

        for idx in range(nevents):
            totalnumevents = nevents-1
            if idx % 100 == 0 and idx > 0:
                print(f'Reading entry: {idx}/{totalnumevents} ({idx / totalnumevents * 100:.2f}%)', end='\r')
            
            ws_before = f.Get(events_before[idx])
            ws_after = f.Get(events_after[idx])
            # Extract the HTmiss value  out of the workspace
            htmiss_before = ws_before.function(htmiss_func_name()).getValV()
            htmiss_after = ws_after.function(htmiss_func_name()).getValV()

            h.Fill(htmiss_before, htmiss_after)
    
    # Once we're done filling the histogram with save it to a new ROOT file
    outpath = pjoin(outdir, 'htmiss_after_reb.root')
    if os.path.exists(outpath):
        outf = r.TFile(outpath, 'UPDATE')
    else:
        raise RuntimeError(f'File does not exist: {outpath}')

    outf.cd()
    h.Write()

    print(f'Histograms saved to: {outpath}')
    return outpath

def plot_htmiss_before_and_after(outdir, infile, dataset_tag='jetht', plot_gen=True):
    '''Do the actual plotting of distributions.'''
    f = uproot.open(infile)
    htmiss_bef = f['htmiss_before']
    htmiss_aft = f['htmiss_after']

    fig, ax = plt.subplots()

    hep.histplot(htmiss_bef.values, htmiss_bef.edges, ax=ax, label='Before rebalancing')
    hep.histplot(htmiss_aft.values, htmiss_aft.edges, ax=ax, label='After rebalancing')

    ax.set_xlabel(r'$H_T^{miss} \ (GeV)$', fontsize=14)
    ax.set_ylabel(r'Counts', fontsize=14)
    ax.set_yscale('log')
    ax.set_ylim(1e-1,1e7)

    ax.legend(title='Rebalancing')

    ax.text(0., 1., f'{tag_to_plottag(dataset_tag)} 2017',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    # If we're looking at QCD and plot_gen=True, plot the GEN HTmiss distribution as well
    if dataset_tag == 'qcd' and plot_gen:
        # Coffea file to take GEN HT-miss distribution from
        accpath = './input/qcd_QCD_HT700to1000-mg_new_pmx_2017.coffea'
        acc = load(accpath)

        distribution = 'gen_htmiss_noweight'
        h = acc[distribution].integrate('dataset').integrate('region', 'inclusive')

        hist.plot1d(h, ax=ax, clear=False)

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels):
        if label == 'None':
            handle.set_label(r'GEN $H_T^{miss}$')

    ax.legend(handles=handles)

    outpath = pjoin(outdir, f'htmiss_before_after_reb.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def plot_htmiss_before_and_after_2d(outdir, infile, dataset_tag='jetht'):
    '''Plot 2D HTmiss before and after histogram.'''
    f = uproot.open(infile)
    h = f['htmiss_2d_before_after']

    fig, ax = plt.subplots()
    pc = ax.pcolormesh(h.edges[0], h.edges[1], h.values.T, norm=colors.LogNorm(1e0,1e3))

    fig.colorbar(pc, ax=ax, label='Counts')

    ax.set_xlabel(r'$H_T^{miss} \ (GeV)$ (before)', fontsize=14)
    ax.set_ylabel(r'$H_T^{miss} \ (GeV)$ (after)', fontsize=14)
    
    ax.text(0., 1., f'{tag_to_plottag(dataset_tag)} 2017',
        fontsize=14,
        ha='left',
        va='bottom',
        transform=ax.transAxes
    )

    outpath = pjoin(outdir, f'htmiss_before_after_reb_2d.pdf')
    fig.savefig(outpath)
    plt.close(fig)
    print(f'File saved: {outpath}')

def main():
    # Point the script to the directory containing the workspace files
    inpath = sys.argv[1]
    infiles = glob.glob(pjoin(inpath, 'ws_eventchunk*.root'))

    jobtag = re.findall('202\d.*', inpath)[0].split('/')[0]

    # Output directory for plotting
    outdir = f'./output/{jobtag}'

    # If the output directory exists, just take the existing ROOT file and do the plotting
    # Otherwise, first save the ROOT file with before/after distributions 
    if os.path.exists(outdir):
        outputrootpath = pjoin(outdir, 'htmiss_after_reb.root')
        print('INFO: ROOT file already exists, moving on to plotting')
    else:
        os.makedirs(outdir)
        outputrootpath = save_htmiss_before_and_after(infiles, outdir)
        save_htmiss_before_and_after_2d(infiles, outdir)

    dataset_tag = 'jetht' if re.match('.*[Jj]et[Hh][Tt].*', inpath) else 'qcd'

    # From the ROOT file created in previous step, plot the distributions
    # (uproot and matplotlib in the house)
    plot_htmiss_before_and_after(outdir, outputrootpath, dataset_tag)

    # Fill and plot 2D HTmiss before and after histogram
    plot_htmiss_before_and_after_2d(outdir, outputrootpath, dataset_tag)

if __name__ == '__main__':
    main()
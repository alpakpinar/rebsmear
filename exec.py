import os
import time
import argparse
import multiprocessing
import numpy as np
from numpy.lib.function_base import extract
import ROOT as r
r.gSystem.Load('libRooFit')
from rebalance import Jet, RebalanceWSFactory
import uproot
from matplotlib import pyplot as plt
from datetime import date
from pprint import pprint

pjoin = os.path.join

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('inpath', help='Path to the input ROOT file.')
    parser.add_argument('--jobname', help='Name of the job.', default=f'{date.today().strftime("%Y-%m-%d")}_rebsmear_run')
    parser.add_argument('--chunksize', help='Number of events for each chunk.', type=int, default=2500)
    parser.add_argument('--dry', help='Dry run, runs over 10 events.', action='store_true')
    parser.add_argument('--ncores', help='Number of cores to use, default is 4.', type=int, default=4)
    parser.add_argument('--dummyjer', help='Placeholder Gaussian width for JER (for testing).', type=float, default=None)
    args = parser.parse_args()
    return args

def read_jets(event, infile):
    t = infile['Events']
    n = event
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])

    # Consider jets with pt > 30 GeV only
    return [Jet(pt=ipt, phi=iphi, eta=ieta) for ipt, iphi, ieta in zip(pt, phi, eta) if ipt>30]


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

def divide_into_chunks(args):
    '''Divide the number of events in the input file into given chunk sizes.'''
    # Read the input file
    infile = uproot.open(args.inpath)

    eventchunksize = args.chunksize

    nevents = len(infile['Events'])
    nchunks = nevents // eventchunksize + 1

    event_chunks = []

    for idx in range(nchunks-1):
        event_chunks.append(
            range(eventchunksize*idx, eventchunksize*(idx+1))
        )

    # The last chunk
    remainder = nevents % eventchunksize
    event_chunks.append(
        range(eventchunksize*(nchunks-1), eventchunksize*(nchunks-1) + remainder)
    )

    return event_chunks

def run_chunk(event_chunk, nchunk, outdir, logdir, args, do_plot=False, do_print=False):
    '''Run rebalancing for chunks of events in the given event chunk.'''
    # Record the running time
    starttime = time.time()

    # Read the input file
    infile = uproot.open(args.inpath)

    jobname = args.jobname
    # Output ROOT file for this event chunk
    f=r.TFile(pjoin(outdir, f"ws_eventchunk_{nchunk}.root"),"RECREATE")

    # Test run
    if args.dry:
        # Run over first 10 events only
        numevents = 10
        event_chunk = range(10*nchunk,10*(nchunk+1))
    else:
        numevents = event_chunk.stop - event_chunk.start

    # Log file for this event chunk
    logf = pjoin(logdir, f'log_eventchunk_{nchunk}.txt')
    with open(logf, 'w+') as logfile:
        logfile.write(f'Starting job, time: {time.ctime()}\n\n')
        logfile.write(f'INFO: Event chunk {nchunk}\n')
        logfile.write(f'INFO: Event range: ({event_chunk.start}, {event_chunk.stop})\n')
        logfile.write(f'INFO: Running on {numevents} events\n')

    # Loop over the events in the chunk
    for event in event_chunk:
        if event % 100 == 0 and event > 0:
            with open(logf, 'a') as logfile:
                logfile.write('*****\n')
                logfile.write(f'Processing event: {event}\n')
                logfile.write(f'Time passed: {time.time() - starttime:.2f} sec\n')

        jets = read_jets(event, infile)
        rbwsfac = RebalanceWSFactory(jets)
        rbwsfac.set_jer_source("./input/jer.root","jer_data",args.dummyjer)
        rbwsfac.build()
        ws = rbwsfac.get_ws()
        if do_print:
            ws.Print("v")

        if do_plot:
            plot_plane(ws, tag=f"{event}_before")
        
        f.cd()
        ws.Write(f'before_{event}')
        m = r.RooMinimizer(ws.function("nll"))
        m.migrad()
        ws.Write(f'rebalanced_{event}')
        if do_plot:
            plot_plane(ws, tag=f"{event}_after")

    with open(logf, 'a') as logfile:
        logfile.write('\n')
        logfile.write(f'Finished job {time.ctime()}\n')
        logfile.write('JOB INFO:\n')
        endtime = time.time()
        timeinterval = endtime - starttime
        timeinterval_per_event = (endtime - starttime) / numevents
        logfile.write(f'Ran over {numevents} events\n')
        logfile.write(f'Total running time: {timeinterval:.3f} s\n')
        logfile.write(f'Running time/event: {timeinterval_per_event:.3f} s\n')

    return ws

def main():
    args = parse_cli()

    if not args.inpath:
        raise RuntimeError('Please provide an input ROOT file.')

    event_chunks = divide_into_chunks(args)
    nchunks = len(event_chunks)

    outdir = f'./output/{args.jobname}'
    logdir = f'./output/{args.jobname}/logs'

    # Do not allow to override an existing job output directory
    if os.path.exists(outdir):
        raise RuntimeError(f'Output directory exists: {outdir}, please remove it first.')

    os.makedirs(outdir)
    os.makedirs(logdir)

    processes = []

    for jobidx in range(args.ncores):
        proc = multiprocessing.Process(target=run_chunk, args=(event_chunks[jobidx], jobidx, outdir, logdir, args))
        proc.start()
        processes.append(proc)

    for process in processes:
        process.join()

if __name__ == "__main__":
    main()
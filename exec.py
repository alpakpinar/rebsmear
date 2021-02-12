#!/usr/bin/env python

import os
import time
import argparse
import multiprocessing
import numpy as np
import uproot
import ROOT as r
r.gSystem.Load('libRooFit')

from numpy.lib.function_base import extract
from helpers.git import git_rev_parse, git_diff
from rebalance import Jet, RebalanceWSFactory, JERLookup
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
    parser.add_argument('--constantjer', help='Placeholder Gaussian width for JER (for testing).', type=float, default=None)
    args = parser.parse_args()
    return args

def read_jets(event, infile, ptmin=30, absetamax=5.0):
    t = infile['Events']
    n = event
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])

    # Return jet collection with pt/eta cuts (if provided)
    return [Jet(pt=ipt, phi=iphi, eta=ieta) for ipt, iphi, ieta in zip(pt, phi, eta) if ( (ipt > ptmin) and (np.abs(ieta) < absetamax) ) ]

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

def run_chunk(event_chunk, nchunk, outdir, logdir, args, do_print=False):
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
        # JER source, initiate the object and specify the JER input
        jer_evaluator = JERLookup()
        if args.constantjer is None:
            jer_evaluator.from_th1("./input/jer.root","jer_data")
        else:
            jer_evaluator.from_constant(args.constantjer)
        rbwsfac.set_jer_evaluator(jer_evaluator)
        rbwsfac.build()
        ws = rbwsfac.get_ws()
        if do_print:
            ws.Print("v")

        f.cd()
        ws.Write(f'before_{event}')
        m = r.RooMinimizer(ws.function("nll"))
        m.migrad()
        ws.Write(f'rebalanced_{event}')

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

    # If directory already exists, do not overwrite, append an additional index
    jobcount = 2
    while os.path.exists(outdir):
        outdir = f'{outdir}_{jobcount}'
        jobcount += 1

    logdir = pjoin(outdir, 'logs')

    os.makedirs(outdir)
    os.makedirs(logdir)

    processes = []

    # Save repo information for this job
    versionfilepath = pjoin(outdir, 'version.txt')
    with open(versionfilepath, 'w+') as f:
        f.write(git_rev_parse() + '\n')
        f.write(git_diff() + '\n')

    # Number of parallel processes, for dry run it is automatically set to 1
    if not args.dry:
        ncores = args.ncores
    else:
        ncores = 1

    for jobidx in range(ncores):
        proc = multiprocessing.Process(target=run_chunk, args=(event_chunks[jobidx], jobidx, outdir, logdir, args))
        proc.start()
        processes.append(proc)

    for process in processes:
        process.join()

if __name__ == "__main__":
    main()

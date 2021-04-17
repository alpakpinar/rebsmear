#!/usr/bin/env python

import os
import re
import time
import argparse
import multiprocessing
import numpy as np
import uproot
import ROOT as r
r.gSystem.Load('libRooFit')

from array import array
from multiprocessing import Pool
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
    parser.add_argument('--nevents', help='Number of events to run on, default is the number of events in the given input file.', type=int, default=None)
    parser.add_argument('--constantjer', help='Placeholder Gaussian width for JER (for testing).', type=float, default=None)
    args = parser.parse_args()
    return args

def read_jets(event, infile, ptmin=30, absetamax=5.0):
    t = infile['Events']
    n = event
    
    pt, phi, eta = (t[f'Jet_{x}'].array(entrystart=n, entrystop=n+1)[0] for x in ['pt','phi','eta'])

    # Return jet collection with pt/eta cuts (if provided)
    return [Jet(pt=ipt, phi=iphi, eta=ieta) for ipt, iphi, ieta in zip(pt, phi, eta) if ( (ipt > ptmin) and (np.abs(ieta) < absetamax) ) ]

def divide_into_chunks(args, outdir, logdir):
    '''Divide the number of events in the input file into given chunk sizes.'''
    # Read the input file
    infile = uproot.open(args.inpath)

    eventchunksize = args.chunksize

    nevents_in_file = len(infile['Events'])

    if args.nevents is not None:
        # Check that the number of events argument provided is within the bounds of the input file
        if args.nevents > nevents_in_file:
            raise RuntimeError(f'Do not have {args.nevents} events in {args.inpath}')
        nevents = args.nevents
    else:
        nevents = nevents_in_file

    nchunks = nevents // eventchunksize + 1

    event_chunks = []

    # Fill in the chunks, together with relevant information
    for idx in range(nchunks-1):
        event_chunks.append({
            'chunk'       : range(eventchunksize*idx, eventchunksize*(idx+1)),
            'nchunk'      : idx,
            'outdir'      : outdir,
            'logdir'      : logdir,
            'filepath'    : args.inpath,
            'constantJER' : args.constantjer,
            }
        )

    # The last chunk
    remainder = nevents % eventchunksize
    if remainder != 0:
        event_chunks.append({
            'chunk'       : range(eventchunksize*(nchunks-1), eventchunksize*(nchunks-1) + remainder),
            'nchunk'      : nchunks-1,
            'outdir'      : outdir,
            'logdir'      : logdir,
            'filepath'    : args.inpath,
            'constantJER' : args.constantjer,
            }
        )

    return event_chunks

def run_chunk(chunk_data):
    '''Run rebalancing for chunks of events in the given event chunk.'''
    # Record the running time
    starttime = time.time()

    # Extract the data
    event_chunk = chunk_data['chunk']
    nchunk = chunk_data['nchunk']
    outdir = chunk_data['outdir']
    logdir = chunk_data['logdir']

    # Read the input file
    infile = uproot.open(chunk_data['filepath'])

    # Output ROOT file for this event chunk
    f=r.TFile(pjoin(outdir, f"ws_eventchunk_{nchunk}.root"),"RECREATE")

    # Output tree to be saved
    nJetMax = 20
    outtree = r.TTree('Events','Events')
    
    njet = array('i', [0])
    jet_pt = array('f',  [0.] * nJetMax)
    jet_eta = array('f', [0.] * nJetMax)
    jet_phi = array('f', [0.] * nJetMax)
    
    htmiss = array('f', [0.])
    ht = array('f', [0.])

    outtree.Branch('njet', njet, 'njet/I')
    outtree.Branch('jet_pt', jet_pt, 'jet_pt[njet]/F')
    outtree.Branch('jet_eta', jet_eta, 'jet_eta[njet]/F')
    outtree.Branch('jet_phi', jet_phi, 'jet_phi[njet]/F')

    outtree.Branch('htmiss', htmiss, 'htmiss/F')
    outtree.Branch('ht', ht, 'ht/F')

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
        if chunk_data['constantJER'] is None:
            jer_evaluator.from_th1("./input/jer.root","jer_mc")
        else:
            jer_evaluator.from_constant(chunk_data['constantJER'])
        rbwsfac.set_jer_evaluator(jer_evaluator)
        rbwsfac.build()
        ws = rbwsfac.get_ws()

        f.cd()
        # ws.Write(f'before_{event}')
        m = r.RooMinimizer(ws.function("nll"))
        m.migrad()
        numjets = int(ws.var('njets').getValV())
        njet[0] = numjets
        for idx in range(numjets):
            jet_pt[idx] = ws.var('gen_pt_{}'.format(idx)).getValV()
            jet_eta[idx] = ws.var('reco_eta_{}'.format(idx)).getValV()
            jet_phi[idx] = ws.var('reco_phi_{}'.format(idx)).getValV()

        # ws.Write(f'rebalanced_{event}')

        htmiss[0] = ws.function('gen_htmiss_pt').getValV()
        ht[0] = ws.function('gen_ht').getValV()

        outtree.Fill()

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

    f.cd()
    outtree.Write()

    return ws

def main():
    args = parse_cli()

    if not args.inpath:
        raise RuntimeError('Please provide an input ROOT file.')

    outdir = f'./output/{args.jobname}'

    # If directory already exists, do not overwrite, append an additional index
    jobcount = 2
    while os.path.exists(outdir):
        jobnumber = re.findall("run(_\d)", outdir)
        if len(jobnumber) == 0:
            outdir = f'{outdir}_2'
        else:
            outdir_basename = re.sub(jobnumber[0], "", outdir)
            outdir = f'{outdir_basename}_{jobcount}'
        jobcount += 1

    logdir = pjoin(outdir, 'logs')

    os.makedirs(outdir)
    os.makedirs(logdir)

    if not args.dry:
        event_chunks = divide_into_chunks(args, outdir, logdir)
    # Test mode, run over first 10 events
    else:
        event_chunks = [{
            'chunk'       : range(0,10),
            'nchunk'      : 0,
            'outdir'      : outdir,
            'logdir'      : logdir,
            'filepath'    : args.inpath,
            'constantJER' : args.constantjer,
        }]
    
    nchunks = len(event_chunks)

    # Save repo information for this job
    versionfilepath = pjoin(outdir, 'version.txt')
    with open(versionfilepath, 'w+') as f:
        f.write(git_rev_parse() + '\n')
        f.write(git_diff() + '\n')

    # Number of cores to use, for dry run it is automatically set to 1
    if not args.dry:
        ncores = args.ncores
        p = Pool(ncores)
    
        res = p.map_async(run_chunk, event_chunks)
        res.wait()
    else:
        for chunk in event_chunks:
            run_chunk(chunk)
    
if __name__ == "__main__":
    main()

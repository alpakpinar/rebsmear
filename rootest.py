import os
import re
import ROOT as r
from matplotlib import pyplot as plt

# Run ROOT in batch mode (no graphic display)
r.gROOT.SetBatch(True)

pjoin = os.path.join

# Dummy histogram
th1 = r.TH1D("test","test",10,0,100)
th1.Fill(5, 3)
th1.Fill(15, 1)
th1.Fill(25, 0.1)

# Elementary variables
for px in [2,4,5,8]:
    px = r.RooRealVar("px","px",px,0,100)

    # Derived variables
    pxsq = r.RooFormulaVar("pxsq","px**2", r.RooArgList(px))

    # Here comes the test:
    # Re-evaluate the value of pxsq as a RooRealVar, then feed into RooDataHist and RooHistPdf
    pxsq_var = r.RooRealVar('pxsqvar', 'pxsqvar', pxsq.evaluate())
    print(pxsq_var)

    rdh = r.RooDataHist("test","test", r.RooArgList(pxsq_var), th1)

    pdf = r.RooHistPdf("pdf",
                    "pdf",
                    r.RooArgSet(pxsq_var),
                    rdh
                )

    # Plot the PDF and save figure
    # frame = pxsq_var.frame(0,100)
    # pdf.plotOn(frame)

    # c = r.TCanvas('test', 'test')
    # frame.Draw()
    # c.SaveAs('test.png')

    print('Current PDF value:')
    print(pdf.getValV())

# Outputs:
# =========================
# Current PDF value:
# 0.3
# RooRealVar::pxsqvar = 16 C  L(-INF - +INF) 

# [#1] INFO:DataHandling -- RooDataHist::adjustBinning(test): fit range of variable pxsqvar expanded to nearest bin boundaries: [-1e+30,1e+30] --> [0,100]
# Current PDF value:
# 0.1
# RooRealVar::pxsqvar = 25 C  L(-INF - +INF) 

# [#1] INFO:DataHandling -- RooDataHist::adjustBinning(test): fit range of variable pxsqvar expanded to nearest bin boundaries: [-1e+30,1e+30] --> [0,100]
# Current PDF value:
# 0.01
# RooRealVar::pxsqvar = 64 C  L(-INF - +INF) 

# [#1] INFO:DataHandling -- RooDataHist::adjustBinning(test): fit range of variable pxsqvar expanded to nearest bin boundaries: [-1e+30,1e+30] --> [0,100]
# Current PDF value:
# 0.0

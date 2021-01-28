import os
import re
import ROOT as r
from matplotlib import pyplot as plt

# Run ROOT in batch mode (no graphic display)
r.gROOT.SetBatch(True)

pjoin = os.path.join

def main():
    # Dummy histogram
    th1 = r.TH1D("test","test",10,0,100)
    th1.Fill(5, 3)
    th1.Fill(15, 1)
    th1.Fill(25, 0.1)

    # Elementary variables
    # for px in [2,4,5,8]:
    # Test value for px
    px=2
    px = r.RooRealVar("px","px",px,0,100)

    # Derived variables
    pxsq = r.RooFormulaVar("pxsq","px**2", r.RooArgList(px))

    # Here comes the test:
    # Re-evaluate the value of pxsq as a RooRealVar, then feed into RooDataHist and RooHistPdf
    pxsq_var = r.RooRealVar('pxsqvar', 'pxsqvar', pxsq.evaluate())
    # pxsq_var = r.RooRealVar('pxsqvar', 'pxsqvar', 10, 100)

    rdh = r.RooDataHist("test","test", r.RooArgList(pxsq_var), th1)

    pdf = r.RooHistPdf("pdf",
                    "pdf",
                    r.RooArgSet(pxsq_var),
                    rdh
                )

    print(f'Value of px: {px}')
    print(f'Value of pxsq: {pxsq}')
    print(f'Value of pxsq_var: {pxsq_var}')
    print(f'PDF: {pdf.getValV()}')

    # Change the px value and see the impact on other variables/PDFs
    print('*'*20)
    print('Setting px=5')
    print('*'*20)
    px.setVal(5)
    print(f'Value of px: {px}')
    print(f'Value of pxsq: {pxsq}')
    print(f'Value of pxsq_var: {pxsq_var}')
    print(f'PDF: {pdf.getValV()}')

    # Plot the PDF and save figure
    # frame = pxsq_var.frame(0,100)
    # pdf.plotOn(frame)

    # c = r.TCanvas('test', 'test')
    # frame.Draw()
    # c.SaveAs('test.png')

if __name__ == '__main__':
    main()

# Outputs:
# =============================
# Value of px: RooRealVar::px = 2  L(0 - 100) 

# Value of pxsq: RooFormulaVar::pxsq[ actualVars=(px) formula="px**2" ] = 4

# Value of pxsq_var: RooRealVar::pxsqvar = 4 C  L(0 - 100) 

# PDF: 0.3
# ********************
# Setting px=5
# ********************
# Value of px: RooRealVar::px = 5  L(0 - 100) 

# Value of pxsq: RooFormulaVar::pxsq[ actualVars=(px) formula="px**2" ] = 25

# Value of pxsq_var: RooRealVar::pxsqvar = 4 C  L(0 - 100) 

# PDF: 0.3

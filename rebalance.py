import ROOT as r
r.gSystem.Load('libRooFit')
import numpy as np
import uproot

@dataclass(frozen=True)
class Jet():
    pt: float
    eta: float
    phi: float
    px: float
    py: float
    pz: float

    def __post_init__(self):
        self.px = np.cos(self.phi) * self.pt
        self.py = np.sin(self.phi) * self.pt
        self.pz = np.sinh(self.eta) * self.pt


class NamingMixin():

    def _name_jet_momentum_pdf(direction, index):
        return f"momentum_pdf_{direction}_{index}"

    def _name_gen_momentum_var(direction, index):
        return f"gen_{direction}_{index}"

    def _name_reco_momentum_var(direction, index):
        return f"reco_{direction}_{index}"
   
    def _name_jet_resolution_var(self, direction, index):
        return f"sigma_{direction}_{index}"



class RebalanceWSFactory(NamingMixin):
    def __init__(self,jets):
        self.jets = jets
        self.njets = len(jets)
        self.ws = r.RooWorkspace()
        self.wsimp = getattr(self.ws, 'import')

    def get_jet(self, index):
        return self.jets[index]

    def build(self):
        self._build_all_jets()

    def _build_all_jets(self):
        for n in range(self.njets):
            self._build_single_jet(n)
        self._build_combined_momentum_pdf()

    def _build_combined_momentum_pdf(self):
        individual_pdf_names = [self._name_jet_momentum_pdf(direction, index) for direction in ('px','py') for index in range(self.njets) ]

        individual_pdfs = [self.ws.function(name) for name in individual_pdf_names]

        pdf_name = self._name_combined_momentum_pdf()
        expression = '*'.join(individual_pdf_names)
        combined_pdf = r.RooGenericPdf(
                    pdf_name,
                    pdf_name,
                    expression,
                    r.RooArgList(*individual_pdfs)
                    )

        self.wsimport(combined_pdf)

    def _build_single_jet_momentum_vars(self, jet, direction, index):
        jet = self.get_jet(index)

        start = getattr(jet, direction)
        lim = min(2*abs(start), 100)

        args = [start, -lim, lim]


        name_gen_var = self._name_gen_momentum_var(direction, index)
        gen_var = r.RooRealVar(
                            name_gen_var,
                            name_gen_var,
                            *args
                            )
        self.wsimp(gen_var)


        name_reco_var = self._name_reco_momentum_var(direction. index)
        reco_var = r.RooRealVar(
                                name_reco_var,
                                name_reco_var,
                                *args
                                )
        self.wsimp(reco_var)

        return (gen_var, reco_var)

    def _resolution(self, index, direction):
        return 0.1 * getattr(self.get_jet(index), direction)

    def _build_single_jet_momentum_pdf(self, gen_var, reco_var, direction, index):
        sigma = self._resolution(index, direction)

        resolution_name = self._name_jet_resolution_var(direction, index)
        resolution_var = r.RooRealVar(
                                 resolution_name,
                                 resolution_name, 
                                 sigma, 
                                 sigma)
        
        pdf_name = self._name_jet_momentum_pdf(direction, index)
        momentum_pdf = r.RooGaussian(
                                    pdf_name,
                                    pdf_name,
                                    reco_var, 
                                    gen_var, 
                                    resolution_var
                                    )

        self.wsimp(momentum_pdf)
        self.wsimp(resolution_var)

    def _build_single_jet(self, index):
        for direction in 'px','py':
            gen_var, reco_var = self._build_single_jet_momentum_vars(direction, index)
            self._build_single_jet_momentum_pdf(gen_var, reco_var, direction, index)

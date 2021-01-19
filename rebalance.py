from dataclasses import dataclass
import ROOT as r
r.gSystem.Load('libRooFit')
import numpy as np


@dataclass(frozen=True)
class Jet():
    pt: float
    eta: float
    phi: float
    px: float = 0
    py: float = 0
    pz: float = 0

    def __post_init__(self):
        object.__setattr__(self, 'px', np.cos(self.phi) * self.pt)
        object.__setattr__(self, 'py', np.sin(self.phi) * self.pt)
        object.__setattr__(self, 'pz', np.sinh(self.eta) * self.pt)


class NamingMixin():

    @classmethod
    def _name_jet_momentum_pdf(self,direction, index):
        return f"momentum_pdf_{direction}_{index}"

    @classmethod
    def _name_gen_momentum_var(self,direction, index):
        return f"gen_{direction}_{index}"
    
    @classmethod
    def _name_reco_momentum_var(self,direction, index):
        return f"reco_{direction}_{index}"

    @classmethod
    def _name_jet_resolution_var(self,direction, index):
        return f"sigma_{direction}_{index}"

    @classmethod
    def _name_partial_gen_htmiss_variable(self,direction):
        return f"gen_htmiss_{direction}"
    
    @classmethod
    def _name_total_gen_htmiss_variable(self):
        return f"gen_htmiss_pt"

    def _name_combined_momentum_pdf(self):
        return f"momentum_pdf_total"

    def _name_likelihood(self):
        return "likelihood"

    
    def _name_total_prior_pdf(self):
        return 'total_prior_pdf'


def make_RooArgList(items):
    l = r.RooArgList()
    for item in items:
        l.add(item)
    return l

class RebalanceWSFactory(NamingMixin):
    '''
    Factory class for a RooWorkspace used for rebalancing fits.

    The class is initiated based on a list of jets.

    jets = [Jet(pt, eta, phi) for pt, eta, phi in ...]
    factory = RebalanceWSFactory(jets)
    factory.build()
    '''
    def __init__(self,jets):
        self.jets = jets
        self.njets = len(jets)
        self.ws = r.RooWorkspace()
        self._wsimp = getattr(self.ws, 'import')
        self._directions = 'px','py'

    def get_ws(self):
        return self.ws

    def get_jet(self, index):
        return self.jets[index]

    def build(self):
        '''
        Defines all ingredients for the fit model.
        '''
        self._build_all_jets()
        self._build_combined_momentum_pdf()
        self._build_priors()
        self._build_likelihood()

    def _build_likelihood(self):
        partial_pdf_names = [
            self._name_total_prior_pdf(),
            self._name_combined_momentum_pdf()
        ]
        partial_pdfs = [self.ws.function(x) for x in partial_pdf_names]

        expression = '*'.join(partial_pdf_names)
        likelihood_name = self._name_likelihood()
        likelihood = r.RooGenericPdf(
            likelihood_name,
            likelihood_name,
            expression,
            r.RooArgList(*partial_pdfs)
        )
        self._wsimp(likelihood)

    def _build_gen_htmiss_variables(self):
        for direction in self._directions:
            self._build_partial_gen_htmiss_variable(direction)
        self._build_total_gen_htmiss_variable()

    def _build_total_gen_htmiss_variable(self):
        partial_htmiss_variable_names = [self._name_partial_gen_htmiss_variable(direction) for direction in self._directions]
        partial_htmiss_variable = [self.ws.function(x) for x in partial_htmiss_variable_names]
        expression = f"sqrt({'+'.join([f'{X}**2' for X in partial_htmiss_variable_names])})"
        total_htmiss_variable = r.RooFormulaVar(
            self._name_total_gen_htmiss_variable(),
            expression,
            make_RooArgList(partial_htmiss_variable)
        )
        self._wsimp(total_htmiss_variable)

    def _build_partial_gen_htmiss_variable(self, direction):
        momentum_variable_names = self._expand_naming(self._name_gen_momentum_var, directions=[direction])
        momentum_variables = [self.ws.var(x) for x  in momentum_variable_names]
        htmiss_variable_name = self._name_partial_gen_htmiss_variable(direction)
        expression = '+'.join(momentum_variable_names)
        partial_htmiss_variable = r.RooFormulaVar(
            htmiss_variable_name,
            expression,
            make_RooArgList(momentum_variables)
        )
        self._wsimp(partial_htmiss_variable)

    def _name_total_gen_htmiss_prior_pdf(self):
        return 'gen_htmiss_prior_pdf'
    
    def _name_total_gen_htmiss_prior_slope(self):
        return 'gen_htmiss_prior_slope'

    def _build_gen_htmiss_prior(self):
        slope_name = self._name_total_gen_htmiss_prior_slope()
        slope_variable = r.RooRealVar(
            slope_name,
            slope_name,
            -0.01,
            -0.01,
            -0.01
        )
        self._wsimp(slope_variable)

        prior_pdf_name = self._name_total_gen_htmiss_prior_pdf()
        htmiss_variable = self.ws.function(self._name_total_gen_htmiss_variable())
        prior_pdf = r.RooExponential(
            prior_pdf_name,
            prior_pdf_name,
            htmiss_variable,
            slope_variable
        )
        self._wsimp(prior_pdf)

    def _build_total_prior(self):
        pdf_name = self._name_total_prior_pdf()
        partial_prior_pdf_names = [self._name_total_gen_htmiss_prior_pdf()]
        partial_prior_pdfs = [self.ws.function(x) for x in partial_prior_pdf_names]
        expression = '*'.join(partial_prior_pdf_names)
        total_prior_pdf = r.RooGenericPdf(
            pdf_name,
            pdf_name,
            expression,
            r.RooArgList(*partial_prior_pdfs)
        )
        self._wsimp(total_prior_pdf)

    def _build_priors(self):
        self._build_gen_htmiss_variables()
        self._build_gen_htmiss_prior()
        self._build_total_prior()

    def _build_all_jets(self):
        '''
        Defines gen->reco PDFs for all jets.
        '''
        for n in range(self.njets):
            self._build_single_jet(n)

    def _expand_naming(self, naming_function, directions=None, indices=None):
        '''
        Creates a list of names for all jets given a pattern defined by the naming function.
        '''
        if directions is None:
            directions = self._directions
        if indices is None:
            indices = range(self.njets)
        return [naming_function(direction, index) for direction in directions for index in indices]

    def _build_combined_momentum_pdf(self):
        '''
        Defines the product PDF of all individual jet PDFs.
        '''
        individual_pdf_names = self._expand_naming(self._name_jet_momentum_pdf)

        individual_pdfs = [self.ws.function(name) for name in individual_pdf_names]

        pdf_name = self._name_combined_momentum_pdf()
        expression = '*'.join(individual_pdf_names)
        combined_pdf = r.RooGenericPdf(
                    pdf_name,
                    pdf_name,
                    expression,
                    make_RooArgList(individual_pdfs)
                    )

        self._wsimp(combined_pdf)

    def _build_single_jet_momentum_vars(self, direction, index):
        '''
        Defines RooRealVars for gen and reco momenta for a given momentum direction and jet index.
        '''
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
        self._wsimp(gen_var)


        name_reco_var = self._name_reco_momentum_var(direction, index)
        reco_var = r.RooRealVar(
                                name_reco_var,
                                name_reco_var,
                                *args
                                )
        self._wsimp(reco_var)

        return (gen_var, reco_var)

    def _resolution(self, index, direction):
        '''
        The jet resolution in a given direction for given jet index.
        '''
        return 0.1 * getattr(self.get_jet(index), direction)

    def _build_single_jet_momentum_pdf(self, gen_var, reco_var, direction, index):
        '''
        Defines the PDF(reco | gen), i.e. the probability representing the agreement
        between gen and reco momentum for a given direction and jet index.
        '''
        sigma = self._resolution(index, direction)
        resolution_name = self._name_jet_resolution_var(direction, index)
        resolution_var = r.RooRealVar(
                                 resolution_name,
                                 resolution_name, 
                                 sigma, 
                                 sigma)
        self._wsimp(resolution_var)
        
        pdf_name = self._name_jet_momentum_pdf(direction, index)
        momentum_pdf = r.RooGaussian(
                                    pdf_name,
                                    pdf_name,
                                    reco_var, 
                                    gen_var, 
                                    resolution_var
                                    )

        self._wsimp(momentum_pdf)

    def _build_single_jet(self, index):
        '''
        Defines variables and PDFs for a single jet index.
        '''
        for direction in self._directions:
            gen_var, reco_var = self._build_single_jet_momentum_vars(direction, index)
            self._build_single_jet_momentum_pdf(gen_var, reco_var, direction, index)

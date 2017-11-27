# -*- coding: utf-8 -*-
import numpy

import environment
from common import UNITS
from interactions.boltzmann import BoltzmannIntegral
from interactions.four_particle.cpp.integral import integration, M_t, grid_t, particle_t, reaction_t


class FourParticleM(object):

    """
    ## Matrix element
    All four-particle interactions of the interest can be rewritten in a form

    \begin{equation}
        |\mathcal{M}|^2 = \sum_{\{i \neq j \neq k \neq l\}} K_1 (p_i \cdot p_j) (p_k \cdot p_l)\
             + K_2 m_i m_j (p_k \cdot p_l)
    \end{equation}
    """
    K1 = 0.
    K2 = 0.
    # Order defines the values of the $(i, j, k, l)$ indices
    order = (0, 1, 2, 3)

    def __init__(self, **kwargs):
        """ Configure matrix element, check that it makes sense """
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if len(set(self.order)) != len(self.order):
            raise Exception("Meaningless order of momenta of the matrix element: {}"
                            .format(self.order))

    def __iadd__(self, M):
        self.K1 += M.K1
        self.K2 += M.K2
        return self

    def __idiv__(self, div):
        self.K1 /= div
        self.K2 /= div
        return self

    def __imul__(self, mul):
        self.K1 *= mul
        self.K2 *= mul
        return self

    def __setattr__(self, name, value):
        if name != 'order':
            return super(FourParticleM, self).__setattr__(name, value)

        self.__dict__['order'] = tuple(sorted(value[:2]) + sorted(value[2:]))

    def __str__(self):
        """ String-like representation of the matrix element """
        ret = ""
        if self.K1:
            ret += "K1={: .2e} ".format(self.K1)
        if self.K2:
            ret += "K2={: .2e} ".format(self.K2)
        return ret + "{}".format(self.order)

    def apply_order(self, order, reaction):
        self.order = order

        # Change the sign of the mass term if related particle has crossed (but not both)
        if bool(reaction[order[0]].crossed) ^ bool(reaction[order[1]].crossed):
            self.K2 *= -1.

    def stackable(self, other):
        return self.order == other.order or \
            (tuple(self.order[2:] + self.order[:2]) == other.order and self.K2 == other.K2 == 0)


class FourParticleIntegral(BoltzmannIntegral):

    creaction = None
    cMs = None

    def __init__(self, **kwargs):
        super(FourParticleIntegral, self).__init__(**kwargs)

    def initialize(self):
        """
        Initialize collision integral constants and save them to the first involved particle
        """
        params = self.particle.params
        if params.T > self.decoupling_temperature and not self.particle.in_equilibrium:
            self.particle.collision_integrals.append(self)

        if self.grids is None:
            self.grids = tuple([self.reaction[1].specie.grid, self.reaction[2].specie.grid])

        self.creaction = None
        self.cMs = None

    def integrate(self, p0, stepsize=None, bounds=None):
        if bounds is None:
            bounds = (
                *self.grids[0].BOUNDS,
                *self.grids[1].BOUNDS
            )

        if stepsize is None:
            stepsize = self.particle.params.h

        if not self.creaction:
            self.creaction = [
                reaction_t(
                    specie=particle_t(
                        m=particle.specie.conformal_mass,
                        grid=grid_t(
                            grid=particle.specie.grid.TEMPLATE,
                            distribution=particle.specie._distribution
                        ),
                        eta=int(particle.specie.eta),
                        in_equilibrium=int(particle.specie.in_equilibrium),
                        T=particle.specie.aT
                    ),
                    side=particle.side
                )
                for particle in self.reaction
            ]

        params = self.particle.params
        constant = (params.m / params.x)**5 / 64. / numpy.pi**3 / params.H
        if not environment.get('LOGARITHMIC_TIMESTEP'):
            constant /= params.x
        self.cMs = [M_t(list(M.order), M.K1 * constant, M.K2 * constant) for M in self.Ms]

        fullstack = numpy.array(integration(p0, *bounds, self.creaction, self.cMs, stepsize))
        return fullstack

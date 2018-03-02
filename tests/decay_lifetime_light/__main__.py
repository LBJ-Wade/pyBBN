# -*- coding: utf-8 -*-


import argparse
import os
from collections import defaultdict

from particles import Particle
from library.SM import particles as SMP
from library.NuMSM import particles as NuP, interactions as NuI
from evolution import Universe
from common import UNITS, Params, utils, LogSpacedGrid


parser = argparse.ArgumentParser(description='Run simulation for given mass and mixing angle')
parser.add_argument('--mass', default=33.9)
parser.add_argument('--theta', default=0.031)
parser.add_argument('--comment', default='')
args = parser.parse_args()

mass = float(args.mass) * UNITS.MeV
theta = float(args.theta)

folder = utils.ensure_dir(
    os.path.split(__file__)[0],
    "output",
    "mass={:e}_theta={:e}".format(mass / UNITS.MeV, theta)
    + args.comment
)


T_initial = 50. * UNITS.MeV
T_final = 0.0008 * UNITS.MeV
params = Params(T=T_initial,
                dy=0.003125)

universe = Universe(params=params, folder=folder)


from common import LinearSpacedGrid
linear_grid = LogSpacedGrid(MOMENTUM_SAMPLES=51, MAX_MOMENTUM=100 * UNITS.MeV)
linear_grid_s = LinearSpacedGrid(MOMENTUM_SAMPLES=51, MAX_MOMENTUM=20 * UNITS.MeV)

photon = Particle(**SMP.photon)

electron = Particle(**SMP.leptons.electron, grid=linear_grid)

neutrino_e = Particle(**SMP.leptons.neutrino_e, grid=linear_grid)
neutrino_mu = Particle(**SMP.leptons.neutrino_mu, grid=linear_grid)
neutrino_tau = Particle(**SMP.leptons.neutrino_tau, grid=linear_grid)

for neutrino in [neutrino_e, neutrino_mu, neutrino_tau]:
    neutrino.decoupling_temperature = 0 * UNITS.MeV

sterile = Particle(**NuP.dirac_sterile_neutrino(mass), grid=linear_grid_s)
sterile.decoupling_temperature = T_initial

universe.add_particles([
    photon,

    electron,

    neutrino_e,
    neutrino_mu,
    neutrino_tau,

    sterile,
])

thetas = defaultdict(float, {
    'tau': theta,
})

interaction = NuI.sterile_leptons_interactions(
    thetas=thetas, sterile=sterile,
    neutrinos=[neutrino_e, neutrino_mu, neutrino_tau],
    # leptons=[]
    leptons=[electron]
)


def reaction_type(reaction):
    return sum(reactant.side for reactant in reaction)


for inter in interaction:
    inter.integrals = [integral for integral in inter.integrals
                       if reaction_type(integral.reaction) == 2]


universe.interactions += (interaction)


def step_monitor(universe):
    for particle in universe.particles:
        if particle.mass > 0 and not particle.in_equilibrium:
            something = particle.conformal_energy(particle.grid.TEMPLATE) / particle.conformal_mass
            integrand = (particle.collision_integral * particle.params.H * something / particle._distribution)
            decay_rate = -integrand
            print(1 / decay_rate.mean() / UNITS.s, decay_rate / UNITS.MeV / 1.10562e-21 / 2, particle.density * universe.params.a**3 / universe.params.S)
            with open(os.path.join(folder, particle.name.replace(' ', '_') + ".decay_rate6.txt"), 'a') as f1:
                f1.write('{:e}'.format(particle.params.T / UNITS.MeV) + '\t'
                         + '{:e}'.format(particle.params.a) + '\t'
                         + '\t'.join(['{:e}'.format(x / UNITS.MeV) for x in decay_rate]) + '\n')


universe.step_monitor = step_monitor

universe.evolve(T_final)

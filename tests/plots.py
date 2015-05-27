import os

import numpy
import matplotlib

from plotting import plt
from common import UNITS, GRID


def articles_comparison_plots(universe, particles):

    """ Ready for copy-paste docstring:

        ### Plots for comparison with articles

        ### JCAP10(2012)014, Figure 9
        <img src="figure_9.svg" width=100% />

        ### JCAP10(2012)014, Figure 10
        <img src="figure_10.svg" width=100% />
        <img src="figure_10_full.svg" width=100% />
    """

    plt.ion()

    """
    ### JCAP10(2012)014, Figure 9
    <img src="figure_9.svg" width=100% />
    """

    plt.figure(9)
    plt.title('Figure 9')
    plt.xlabel('MeV/T')
    plt.ylabel(u'aT')
    plt.xscale('log')
    plt.xlim(0.5, UNITS.MeV/universe.params.T_final)
    plt.xticks([1, 2, 3, 5, 10, 20])
    plt.axes().get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    plt.plot(UNITS.MeV / numpy.array(universe.data['T']),
             numpy.array(universe.data['aT']) / UNITS.MeV)
    plt.show()
    plt.savefig(os.path.join(universe.folder, 'figure_9.svg'))

    """
    ### JCAP10(2012)014, Figure 10
    <img src="figure_10.svg" width=100% />
    <img src="figure_10_full.svg" width=100% />
    """

    plt.figure(10)
    plt.title('Figure 10')
    plt.xlabel('Conformal momentum y = pa')
    plt.ylabel('f/f_eq')
    plt.xlim(0, 20)

    # Distribution functions arrays
    distributions_file = open(os.path.join(universe.folder, 'distributions.txt'), "w")

    for neutrino in particles:
        f = neutrino._distribution
        feq = neutrino.equilibrium_distribution()
        plt.plot(GRID.TEMPLATE/UNITS.MeV, f/feq, label=neutrino.name)

        numpy.savetxt(distributions_file, (f, feq, f/feq), header=str(neutrino),
                      footer='-'*80, fmt="%1.5e")

    plt.legend()
    plt.draw()
    plt.show()
    plt.savefig(os.path.join(universe.folder, 'figure_10_full.svg'))

    plt.xlim(0, 10)
    plt.ylim(0.99, 1.06)
    plt.draw()
    plt.show()
    plt.savefig(os.path.join(universe.folder, 'figure_10.svg'))

    distributions_file.close()

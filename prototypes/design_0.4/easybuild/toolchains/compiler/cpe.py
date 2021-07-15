##
# Copyright 2014-2020 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
Support for the Cray Programming Environment (craype) compiler drivers (aka cc, CC, ftn).

The basic concept is that the compiler driver knows how to invoke the true underlying
compiler with the compiler's specific options tuned to Cray systems.

That means that certain defaults are set that are specific to Cray's computers.

The compiler drivers are quite similar to EB toolchains as they include
linker and compiler directives to use the Cray libraries for their MPI (and network drivers)
Cray's LibSci (BLAS/LAPACK et al), FFT library, etc.

:author: Petar Forai (IMP/IMBA, Austria)
:author: Kenneth Hoste (Ghent University)
:author: Kurt Lust (University of Antwerpen)
"""
import copy

import easybuild.tools.environment as env
from easybuild.toolchains.compiler.aocc import TC_CONSTANT_AOCC, Aocc
from easybuild.toolchains.compiler.gcc import TC_CONSTANT_GCC, Gcc
from easybuild.toolchains.compiler.inteliccifort import TC_CONSTANT_INTELCOMP, IntelIccIfort
from easybuild.toolchains.compiler.pgi import TC_CONSTANT_PGI, Pgi
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.config import build_option
from easybuild.tools.toolchain.compiler import Compiler


TC_CONSTANT_CPE = "CPE"
TC_CONSTANT_CCE = "CCE"


class cpeCompiler(Compiler):
    """Generic support for using Cray compiler drivers."""
    TOOLCHAIN_FAMILY = TC_CONSTANT_CPE

    # compiler module name is PrgEnv, suffix name depends on CrayPE flavor (gnu, intel, cray)
    COMPILER_MODULE_NAME = None
    # compiler family depends on CrayPE flavor
    COMPILER_FAMILY = None

    COMPILER_UNIQUE_OPTS = {
        'dynamic': (True, "Generate dynamically linked executable"),
        'mpich-mt': (False, "Directs the driver to link in an alternate version of the Cray-MPICH library which \
                             provides fine-grained multi-threading support to applications that perform \
                             MPI operations within threaded regions."),
        'optarch': (False, "Enable architecture optimizations"),
        'verbose': (True, "Verbose output"),
    }

    COMPILER_UNIQUE_OPTION_MAP = {
        # handle shared and dynamic always via $CRAYPE_LINK_TYPE environment variable, don't pass flags to wrapper
        'shared': '',
        'dynamic': '',
        'verbose': 'craype-verbose',
        'mpich-mt': 'craympich-mt',
        'openmp': {True: 'openmp', False: 'noopenmp'},  # Cray compiler wrapper option to ensure it works with all compilers.
    }

    COMPILER_CC = 'cc'
    COMPILER_CXX = 'CC'

    COMPILER_F77 = 'ftn'
    COMPILER_F90 = 'ftn'
    COMPILER_FC = 'ftn'

    # suffix for PrgEnv module that matches this toolchain
    # e.g. 'gnu' => 'PrgEnv-gnu/<version>'
    PRGENV_MODULE_NAME_SUFFIX = None

    # template for craype module (determines code generator backend of Cray compiler wrappers)
    CRAYPE_MODULE_NAME_TEMPLATE = 'craype-%(optarch)s'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(cpeCompiler, self).__init__(*args, **kwargs)
        # 'register'  additional toolchain options that correspond to a compiler flag
        self.COMPILER_FLAGS.extend(['dynamic', 'mpich-mt'])

        # use name of PrgEnv module as name of module that provides compiler
        self.COMPILER_MODULE_NAME = ['cpe%s' % self.CPE_MODULE_NAME_SUFFIX]

        # copy unique option map, since we fiddle with it later
        self.COMPILER_UNIQUE_OPTION_MAP = copy.deepcopy(self.COMPILER_UNIQUE_OPTION_MAP)

    def _set_optimal_architecture(self):
        """Load craype module specified via 'optarch' build option."""
        optarch = build_option('optarch')
        if optarch is None:
            raise EasyBuildError("Don't know which 'craype' module to load, 'optarch' build option is unspecified.")
        else:
            craype_mod_name = self.CRAYPE_MODULE_NAME_TEMPLATE % {'optarch': optarch}
            if self.modules_tool.exist([craype_mod_name], skip_avail=True)[0]:
                self.modules_tool.load([craype_mod_name])
            else:
                raise EasyBuildError("Necessary craype module with name '%s' is not available (optarch: '%s')",
                                     craype_mod_name, optarch)

        # no compiler flag when optarch toolchain option is enabled
        self.options.options_map['optarch'] = ''

    def prepare(self, *args, **kwargs):
        """Prepare to use this toolchain; define $CRAYPE_LINK_TYPE if 'dynamic' toolchain option is enabled."""
        super(cpeCompiler, self).prepare(*args, **kwargs)

        if self.options['dynamic'] or self.options['shared']:
            self.log.debug("Enabling building of shared libs/dynamically linked executables via $CRAYPE_LINK_TYPE")
            env.setvar('CRAYPE_LINK_TYPE', 'dynamic')


class cpeAOCC(cpeCompiler):
    """Support for using the Cray AOCC compiler wrappers."""
    PRGENV_MODULE_NAME_SUFFIX = 'aocc'  # PrgEnv-aocc
    CPE_MODULE_NAME_SUFFIX =    'AMD'   # cpeAMD
    COMPILER_FAMILY = TC_CONSTANT_AOCC

    def __init__(self, *args, **kwargs):
        """cpeAOCC constructor."""
        super(cpeAOCC, self).__init__(*args, **kwargs)
        for precflag in self.COMPILER_PREC_FLAGS:
            self.COMPILER_UNIQUE_OPTION_MAP[precflag] = Aocc.COMPILER_UNIQUE_OPTION_MAP[precflag]


class cpeCCE(cpeCompiler):
    """Support for using the Cray CCE compiler wrappers."""
    PRGENV_MODULE_NAME_SUFFIX = 'cray'  # PrgEnv-cray
    CPE_MODULE_NAME_SUFFIX =    'Cray'  # cpeCray
    COMPILER_FAMILY = TC_CONSTANT_CCE

    def __init__(self, *args, **kwargs):
        """cpeCray constructor."""
        super(cpeCCE, self).__init__(*args, **kwargs)
        for precflag in self.COMPILER_PREC_FLAGS:
            self.COMPILER_UNIQUE_OPTION_MAP[precflag] = []


class cpeGCC(cpeCompiler):
    """Support for using the Cray GNU compiler wrappers."""
    PRGENV_MODULE_NAME_SUFFIX = 'gnu'  # PrgEnv-gnu
    CPE_MODULE_NAME_SUFFIX =    'GNU'  # cpeGNU
    COMPILER_FAMILY = TC_CONSTANT_GCC

    def __init__(self, *args, **kwargs):
        """cpeGCC constructor."""
        super(cpeGCC, self).__init__(*args, **kwargs)
        for precflag in self.COMPILER_PREC_FLAGS:
            self.COMPILER_UNIQUE_OPTION_MAP[precflag] = Gcc.COMPILER_UNIQUE_OPTION_MAP[precflag]


class cpeICC(cpeCompiler):
    """Support for using the Cray Intel compiler wrappers."""
    PRGENV_MODULE_NAME_SUFFIX = 'intel'  # PrgEnv-intel
    CPE_MODULE_NAME_SUFFIX =    'Intel'  # cpeIntel
    COMPILER_FAMILY = TC_CONSTANT_INTELCOMP

    def __init__(self, *args, **kwargs):
        """cpeINTEL constructor."""
        super(cpeICC, self).__init__(*args, **kwargs)
        for precflag in self.COMPILER_PREC_FLAGS:
            self.COMPILER_UNIQUE_OPTION_MAP[precflag] = IntelIccIfort.COMPILER_UNIQUE_OPTION_MAP[precflag]

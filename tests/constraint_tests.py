from difflib import unified_diff
import logging
import os.path as ospath
import re

from nose.tools import eq_, assert_raises
import numpy as np
import pandas as pd

from oemof.solph.network import Investment
from oemof.solph import OperationalModel

from oemof.core import energy_system as core_es
import oemof.solph as solph

from oemof.solph import (Bus, Source, Sink, Flow, LinearTransformer, Storage)
from oemof.tools import create_components as cc, helpers

logging.disable(logging.INFO)


class Constraint_Tests:

    @classmethod
    def setUpClass(self):

        self.objective_pattern = re.compile("^objective.*(?=s\.t\.)",
                                            re.DOTALL|re.MULTILINE)

        self.date_time_index = pd.date_range('1/1/2012', periods=3, freq='H')

        self.tmppath = helpers.extend_basic_path('tmp')
        logging.info(self.tmppath)

    def setup(self):
        self.energysystem = core_es.EnergySystem(groupings=solph.GROUPINGS,
                                                 time_idx=self.date_time_index)

    def compare_lp_files(self, energysystem, filename, ignored=None):
        om = OperationalModel(energysystem,
                              timeindex=self.energysystem.time_idx)
        tmp_filename = filename.replace('.lp', '') + '_tmp.lp'
        new_filename = ospath.join(self.tmppath, tmp_filename)
        om.write(new_filename, io_options={'symbolic_solver_labels': True})
        logging.info("Comparing with file: {0}".format(filename))
        with open(ospath.join(self.tmppath, tmp_filename)) as generated_file:
            with open(ospath.join(ospath.dirname(ospath.realpath(__file__)),
                                  "lp_files",
                                  filename)) as expected_file:

                def chop_trailing_whitespace(lines):
                    return [re.sub("\s*$", '', l) for l in lines]

                def remove(pattern, lines):
                    if not pattern:
                        return lines
                    return re.subn(pattern, "", "\n".join(lines))[0].split("\n")

                expected = remove(ignored,
                                  chop_trailing_whitespace(
                                      expected_file.readlines()))
                generated = remove(ignored,
                                   chop_trailing_whitespace(
                                       generated_file.readlines()))
                eq_(generated, expected,
                    "Failed matching expected with generated lp file:\n" +
                    "\n".join(unified_diff(expected, generated,
                                           fromfile=ospath.relpath(
                                               expected_file.name),
                                           tofile=ospath.basename(
                                               generated_file.name),
                                           lineterm="")))

    def test_linear_transformer(self):
        """Test LinearTransformer without Investment."""

        bgas = Bus(label="gas")

        bel = Bus(label="electricity")

        LinearTransformer(
            label="powerplant_gas",
            inputs={bgas: Flow()},
            outputs={bel: Flow(nominal_value=10e10, variable_costs=50)},
            conversion_factors={bel: 0.58})

        self.compare_lp_files(self.energysystem, "transformer_linear.lp",
                              ignored=self.objective_pattern)

    # def test_linear_transformer_invest(self):
    #     """Test LinearTransformer with Investment."""
    #
    #     bgas = Bus(label="gas")
    #
    #     bel = Bus(label="electricity")
    #
    #     LinearTransformer(
    #         label="powerplant_gas",
    #         inputs={bgas: Flow()},
    #         outputs={bel: Flow(variable_costs=50,
    #                            investment=Investment(ep_costs=80, maximum=4e10))
    #                  },
    #         conversion_factors={bel: 0.58})
    #
    #     self.compare_lp_files(self.energysystem, "transformer_simp_invest.lp",
    #                           ignored=self.objective_pattern)

    def test_source_fixed(self):
        """Test Source without investment."""

        bel = Bus(uid="bel", type="el")

        Source(label='wind', outputs={bel: Flow(actual_value=[50, 80, 30],
                                                nominal_value=1000000,
                                                fixed=True, fixed_costs=20)})

        self.compare_lp_files(self.energysystem, "source_fixed.lp",
                              ignored=self.objective_pattern)

    def test_storage(self):
        pass

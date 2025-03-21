# Copyright 2024 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests current diffusion implementation."""


CONFIG = {
    'runtime_params': {
        'profile_conditions': {
            'ne_bound_right': 0.5,
            'set_pedestal': False,
            # set flat Ohmic current for larger range of current evolution
            # for test
            'nu': 0,
        },
        'numerics': {
            'ion_heat_eq': False,
            'el_heat_eq': False,
            'current_eq': True,
            'resistivity_mult': 100,  # to shorten current diffusion time
            't_final': 3,
        },
    },
    'geometry': {
        'geometry_type': 'circular',
    },
    'sources': {
        'j_bootstrap': {
            'bootstrap_mult': 0.0,
        },
        'generic_ion_el_heat_source': {},
        'generic_particle_source': {},
        'gas_puff_source': {},
        'pellet_source': {},
        'generic_current_source': {},
    },
    'pedestal': {},
    'transport': {
        'transport_model': 'constant',
    },
    'stepper': {
        'stepper_type': 'linear',
        'predictor_corrector': False,
    },
    'time_step_calculator': {
        'calculator_type': 'chi',
    },
}

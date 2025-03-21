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

"""Pydantic config for source models."""

from collections.abc import Mapping
import copy
from typing import Any, Union

import pydantic
from torax.sources import bootstrap_current_source
from torax.sources import bremsstrahlung_heat_sink
from torax.sources import cyclotron_radiation_heat_sink
from torax.sources import electron_cyclotron_source
from torax.sources import fusion_heat_source
from torax.sources import gas_puff_source
from torax.sources import generic_current_source
from torax.sources import generic_ion_el_heat_source
from torax.sources import generic_particle_source
from torax.sources import ion_cyclotron_source
from torax.sources import ohmic_heat_source
from torax.sources import pellet_source
from torax.sources import qei_source
from torax.sources.impurity_radiation_heat_sink import impurity_radiation_constant_fraction
from torax.sources.impurity_radiation_heat_sink import impurity_radiation_mavrin_fit
from torax.torax_pydantic import torax_pydantic
from typing_extensions import Annotated


def get_impurity_heat_sink_discriminator_value(model: dict[str, Any]) -> str:
  """Returns the discriminator value for a given model."""
  # Default to impurity_radiation_mavrin_fit if no model_func is specified.
  return model.get('model_func', 'impurity_radiation_mavrin_fit')


ImpurityRadiationHeatSinkConfig = Annotated[
    Union[
        Annotated[
            impurity_radiation_mavrin_fit.ImpurityRadiationHeatSinkMavrinFitConfig,
            pydantic.Tag('impurity_radiation_mavrin_fit'),
        ],
        Annotated[
            impurity_radiation_constant_fraction.ImpurityRadiationHeatSinkConstantFractionConfig,
            pydantic.Tag('radially_constant_fraction_of_Pin'),
        ],
    ],
    pydantic.Field(
        discriminator=pydantic.Discriminator(
            get_impurity_heat_sink_discriminator_value
        )
    ),
]

SourceModelConfig = Union[
    bootstrap_current_source.BootstrapCurrentSourceConfig,
    bremsstrahlung_heat_sink.BremsstrahlungHeatSinkConfig,
    cyclotron_radiation_heat_sink.CyclotronRadiationHeatSinkConfig,
    electron_cyclotron_source.ElectronCyclotronSourceConfig,
    gas_puff_source.GasPuffSourceConfig,
    generic_particle_source.GenericParticleSourceConfig,
    pellet_source.PelletSourceConfig,
    fusion_heat_source.FusionHeatSourceConfig,
    generic_current_source.GenericCurrentSourceConfig,
    generic_ion_el_heat_source.GenericIonElHeatSourceConfig,
    ImpurityRadiationHeatSinkConfig,
    ion_cyclotron_source.IonCyclotronSourceConfig,
    ohmic_heat_source.OhmicHeatSourceConfig,
    qei_source.QeiSourceConfig,
]


class Sources(torax_pydantic.BaseModelFrozen):
  """Config for source models.

  The `from_dict` method of constructing this class supports the config
  described in: https://torax.readthedocs.io/en/latest/configuration.html
  """
  source_model_config: Mapping[str, SourceModelConfig] = pydantic.Field(
      discriminator='source_name'
  )

  @pydantic.model_validator(mode='before')
  @classmethod
  def _conform_data(cls, data: dict[str, Any]) -> dict[str, Any]:
    # If we are running with the standard class constructor we don't need to do
    # any custom validation.
    if 'source_model_config' in data:
      return data

    constructor_data = copy.deepcopy(data)
    for key in data.keys():
      constructor_data[key].update({'source_name': key})

    return {'source_model_config': constructor_data}

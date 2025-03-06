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
"""Impurity radiation heat sink for electron heat equation based on constant fraction of total power density."""
from __future__ import annotations

import dataclasses
from typing import Literal

import chex
import jax.numpy as jnp
from torax import array_typing
from torax import interpolated_param
from torax import math_utils
from torax import state
from torax.config import runtime_params_slice
from torax.geometry import geometry
from torax.sources import runtime_params as runtime_params_lib
from torax.sources import source_profiles as source_profiles_lib
from torax.torax_pydantic import torax_pydantic

MODEL_FUNCTION_NAME = 'radially_constant_fraction_of_Pin'


def radially_constant_fraction_of_Pin(  # pylint: disable=invalid-name
    unused_static_runtime_params_slice: runtime_params_slice.StaticRuntimeParamsSlice,
    dynamic_runtime_params_slice: runtime_params_slice.DynamicRuntimeParamsSlice,
    geo: geometry.Geometry,
    source_name: str,
    unused_core_profiles: state.CoreProfiles,
    calculated_source_profiles: source_profiles_lib.SourceProfiles | None,
) -> tuple[chex.Array, ...]:
  """Model function for radiation heat sink from impurities.

  This model represents a sink in the temp_el equation, whose value is a fixed %
  of the total heating power input.

  Args:
    unused_static_runtime_params_slice: Static runtime parameters.
    dynamic_runtime_params_slice: Dynamic runtime parameters.
    geo: Geometry object.
    source_name: Name of the source.
    unused_core_profiles: Core profiles object.
    calculated_source_profiles: Source profiles which have already been
      calculated and can be used to avoid recomputing them.

  Returns:
    The heat sink profile.
  """
  dynamic_source_runtime_params = dynamic_runtime_params_slice.sources[
      source_name
  ]
  assert isinstance(dynamic_source_runtime_params, DynamicRuntimeParams)

  if calculated_source_profiles is None:
    raise ValueError(
        'calculated_source_profiles is a required argument for'
        ' `radially_constant_fraction_of_Pin`. This can occur if this source'
        ' function is used in an explicit source.'
    )

  # Based on source_models.sum_sources_temp_el and source_models.calc_and_sum
  # sources_psi, but only summing over heating *input* sources
  # (Pohm + Paux + Palpha + ...) and summing over *both* ion + electron heating

  # TODO(b/383061556) Move away from using brittle source names to identify
  # sinks/sources.
  source_profiles = jnp.zeros_like(geo.rho)
  for source_name in calculated_source_profiles.temp_el:
    if 'sink' not in source_name:
      source_profiles += calculated_source_profiles.temp_el[source_name]
  for source_name in calculated_source_profiles.temp_ion:
    if 'sink' not in source_name:
      source_profiles += calculated_source_profiles.temp_ion[source_name]

  Qtot_in = source_profiles
  Ptot_in = math_utils.cell_integration(Qtot_in * geo.vpr, geo)
  Vtot = geo.volume_face[-1]

  # Calculate the heat sink as a fraction of the total power input
  return (
      -dynamic_source_runtime_params.fraction_of_total_power_density
      * Ptot_in
      / Vtot
      * jnp.ones_like(geo.rho),
  )


class ImpurityRadiationHeatSinkConstantFractionConfig(
    runtime_params_lib.SourceModelBase
):
  """Configuration for the ImpurityRadiationHeatSink.

  Attributes:
    fraction_of_total_power_density: Fraction of total power density to be
      absorbed by the impurity.
  """
  source_name: Literal['impurity_radiation_heat_sink'] = (
      'impurity_radiation_heat_sink'
  )
  model_func: Literal['radially_constant_fraction_of_Pin'] = (
      'radially_constant_fraction_of_Pin'
  )
  fraction_of_total_power_density: torax_pydantic.TimeVaryingScalar = (
      torax_pydantic.ValidatedDefault(0.1)
  )
  mode: runtime_params_lib.Mode = runtime_params_lib.Mode.MODEL_BASED


@dataclasses.dataclass(kw_only=True)
class RuntimeParams(runtime_params_lib.RuntimeParams):
  fraction_of_total_power_density: runtime_params_lib.TimeInterpolatedInput = (
      0.1
  )
  mode: runtime_params_lib.Mode = runtime_params_lib.Mode.MODEL_BASED

  def make_provider(
      self,
      torax_mesh: geometry.Grid1D | None = None,
  ) -> RuntimeParamsProvider:
    return RuntimeParamsProvider(**self.get_provider_kwargs(torax_mesh))


@chex.dataclass
class RuntimeParamsProvider(runtime_params_lib.RuntimeParamsProvider):
  """Provides runtime parameters for a given time and geometry."""

  fraction_of_total_power_density: interpolated_param.InterpolatedVarSingleAxis

  def build_dynamic_params(
      self,
      t: chex.Numeric,
  ) -> DynamicRuntimeParams:
    return DynamicRuntimeParams(**self.get_dynamic_params_kwargs(t))


@chex.dataclass(frozen=True)
class DynamicRuntimeParams(runtime_params_lib.DynamicRuntimeParams):
  fraction_of_total_power_density: array_typing.ScalarFloat

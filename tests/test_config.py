"""Tests for immutable experiment configurations."""

from dataclasses import replace

import pytest

from bah_cascade.config import (
    DEMO,
    PILOT,
    SMOKE,
    CascadeConfig,
    DesignConfig,
    NetworkConfig,
)


def test_config_hash_has_eight_hex_characters_when_config_is_valid() -> None:
    value = DEMO.config_hash()

    assert len(value) == 8
    int(value, 16)


def test_config_hash_is_stable_when_config_is_unchanged() -> None:
    assert DEMO.config_hash() == DEMO.config_hash()


def test_config_hash_changes_when_replicates_change() -> None:
    assert replace(DEMO, replicates=2).config_hash() != DEMO.config_hash()


def test_network_config_rejects_n1_below_seed_size_when_m_is_large() -> None:
    with pytest.raises(ValueError):
        NetworkConfig(n1=8, n2=5, m_values=(4,))


def test_network_config_accepts_n1_equal_to_seed_size_when_m_is_four() -> None:
    config = NetworkConfig(n1=12, n2=5, m_values=(4,))

    assert config.n1 == 12


def test_design_config_rejects_homophily_above_one_when_grid_is_invalid() -> None:
    with pytest.raises(ValueError):
        DesignConfig(
            name="INVALID",
            h_values=(1.2,),
            p_values=(0.4,),
            network=NetworkConfig(n1=20, n2=10, m_values=(1,)),
            cascade=CascadeConfig(phi_values=(0.15,)),
            replicates=1,
            design="custom",
            interventions=((0.2, 0.4),),
        )


def test_design_config_rejects_custom_design_without_interventions_when_constructed() -> None:
    with pytest.raises(ValueError):
        DesignConfig(
            name="INVALID",
            h_values=(0.8,),
            p_values=(0.4,),
            network=NetworkConfig(n1=20, n2=10, m_values=(1,)),
            cascade=CascadeConfig(phi_values=(0.15,)),
            replicates=1,
            design="custom",
        )


def test_pilot_parameters_report_seventy_five_baselines_when_full_design() -> None:
    parameters = PILOT.parameters()

    assert parameters["baselines"] == 75
    assert parameters["interventions_per_baseline"] == 24


def test_pilot_interventions_for_include_twenty_four_targets_when_full_design() -> None:
    assert len(PILOT.interventions_for(0.2, 0.4)) == 24


def test_demo_matches_roadmap_values_when_defined() -> None:
    assert DEMO.network.n1 == 50
    assert DEMO.network.n2 == 50
    assert DEMO.network.m_values == (1,)
    assert DEMO.h_values == (0.8,)
    assert DEMO.p_values == (0.4,)
    assert DEMO.cascade.phi_values == (0.15,)


def test_smoke_matches_agreed_values_when_defined() -> None:
    assert SMOKE.network.n1 == 20
    assert SMOKE.network.n2 == 10
    assert SMOKE.interventions_for(0.8, 0.4) == ((0.2, 0.4),)

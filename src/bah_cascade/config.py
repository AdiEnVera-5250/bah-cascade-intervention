"""Immutable experiment configurations and canonical hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

DesignKind = Literal["full", "reduced", "custom"]
Intervention = tuple[float, float]

H_VALUES: tuple[float, ...] = (0.0, 0.2, 0.5, 0.8, 1.0)
P_VALUES: tuple[float, ...] = (0.2, 0.4, 0.5, 0.6, 0.8)
M_VALUES: tuple[int, ...] = (1, 2, 4)
PHI_VALUES: tuple[float, ...] = (0.10, 0.15, 0.20, 0.25)


def _validate_probabilities(values: tuple[float, ...], name: str) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")
    for value in values:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} values must lie in [0, 1], got {value!r}")


def _validate_sorted_unique(values: tuple[object, ...], name: str) -> None:
    if values != tuple(sorted(values)) or len(set(values)) != len(values):
        raise ValueError(f"{name} must be sorted and unique")


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    """Sizes and arriving-edge counts shared by every baseline."""

    n1: int
    n2: int
    m_values: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.m_values:
            raise ValueError("m_values must not be empty")
        if any(m < 1 for m in self.m_values):
            raise ValueError("every m value must be at least 1")
        _validate_sorted_unique(self.m_values, "m_values")
        if self.n2 <= 0:
            raise ValueError("n2 must be positive")
        if self.n1 < 2 * (max(self.m_values) + 2):
            raise ValueError("n1 must fit the largest seed graph")


@dataclass(frozen=True, slots=True)
class CascadeConfig:
    """Homogeneous threshold grid."""

    phi_values: tuple[float, ...]

    def __post_init__(self) -> None:
        _validate_probabilities(self.phi_values, "phi_values")
        _validate_sorted_unique(self.phi_values, "phi_values")


@dataclass(frozen=True, slots=True)
class DesignConfig:
    """Resolved experimental design."""

    name: str
    h_values: tuple[float, ...]
    p_values: tuple[float, ...]
    network: NetworkConfig
    cascade: CascadeConfig
    replicates: int
    design: DesignKind
    interventions: tuple[Intervention, ...] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")
        _validate_probabilities(self.h_values, "h_values")
        _validate_probabilities(self.p_values, "p_values")
        _validate_sorted_unique(self.h_values, "h_values")
        _validate_sorted_unique(self.p_values, "p_values")
        if self.replicates < 1:
            raise ValueError("replicates must be at least 1")
        if self.design not in ("full", "reduced", "custom"):
            raise ValueError(f"unknown design: {self.design!r}")
        if self.design == "custom":
            if not self.interventions:
                raise ValueError("custom designs require explicit interventions")
            _validate_sorted_unique(self.interventions, "interventions")
            for h2, p2 in self.interventions:
                _validate_probabilities((h2, p2), "interventions")
        elif self.interventions is not None:
            raise ValueError("full and reduced designs derive their interventions")

        counts = {
            len(self.interventions_for(h1, p1)) for h1 in self.h_values for p1 in self.p_values
        }
        if len(counts) != 1:
            raise ValueError("every baseline must have the same number of interventions")

    def interventions_for(self, h1: float, p1: float) -> tuple[Intervention, ...]:
        """Return the phase-2 targets paired with a baseline, excluding its control."""
        if self.design == "custom":
            assert self.interventions is not None
            targets = self.interventions
        else:
            targets_list: list[Intervention] = []
            for h2 in self.h_values:
                for p2 in self.p_values:
                    if h2 == h1 and p2 == p1:
                        continue
                    if self.design == "reduced" and h2 != h1 and p2 != p1:
                        continue
                    targets_list.append((h2, p2))
            targets = tuple(targets_list)
        return tuple(target for target in targets if target != (h1, p1))

    def parameters(self) -> dict[str, object]:
        """Return the resolved design in the shape required by ``metadata.json``."""
        baselines = len(self.h_values) * len(self.p_values) * len(self.network.m_values)
        counts = {
            len(self.interventions_for(h1, p1)) for h1 in self.h_values for p1 in self.p_values
        }
        return {
            "H": list(self.h_values),
            "P": list(self.p_values),
            "M": list(self.network.m_values),
            "Phi": list(self.cascade.phi_values),
            "N1": self.network.n1,
            "N2": self.network.n2,
            "N": self.network.n1 + self.network.n2,
            "R": self.replicates,
            "design": self.design,
            "baselines": baselines,
            "interventions_per_baseline": counts.pop(),
        }

    def canonical_json(self) -> str:
        """Serialize the resolved configuration deterministically."""
        return json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )

    def config_hash(self) -> str:
        """Return the eight-character hexadecimal configuration hash."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()[:8]


PILOT = DesignConfig(
    name="PILOT",
    h_values=H_VALUES,
    p_values=P_VALUES,
    network=NetworkConfig(n1=250, n2=250, m_values=M_VALUES),
    cascade=CascadeConfig(phi_values=PHI_VALUES),
    replicates=50,
    design="full",
)

DEMO = DesignConfig(
    name="DEMO",
    h_values=(0.5,),
    p_values=(0.2,),
    network=NetworkConfig(n1=250, n2=250, m_values=(2,)),
    cascade=CascadeConfig(phi_values=(0.15,)),
    replicates=100,
    design="custom",
    interventions=((0.0, 0.2), (1.0, 0.2)),
)

SMOKE = DesignConfig(
    name="SMOKE",
    h_values=(0.8,),
    p_values=(0.4,),
    network=NetworkConfig(n1=20, n2=10, m_values=(1,)),
    cascade=CascadeConfig(phi_values=(0.15,)),
    replicates=1,
    design="custom",
    interventions=((0.2, 0.4),),
)

# config

**Fase:** 1 (pendiente de autorización).
**Estado:** sin implementar.

Convierte un módulo Python de configuración en una lista de celdas de experimento
validadas y congeladas. Es la única puerta de entrada de parámetros al sistema: no
hay números mágicos en el resto del paquete.

## Contrato de un módulo de configuración

```python
# configs/ejemplo.py
DESIGN: dict[str, tuple] = {...}                      # factores; {} = una sola celda

def build_experiment(params: dict[str, float]) -> Experiment: ...
```

Requisitos que valida el loader:

1. Ambas variables existen y tienen el tipo esperado.
2. `build_experiment` es puro: dos llamadas con los mismos parámetros producen
   configuraciones equivalentes.
3. Los parámetros recibidos son exactamente las claves de `DESIGN`.
4. Las condiciones comparten parámetros de prefijo (necesario para el
   emparejamiento).

## Módulos

### `schema.py`

Dataclasses inmutables que describen el experimento.

| Tipo | Campos principales |
|---|---|
| `RunSpec` | `name`, `seed`, `output_dir` |
| `InitialGraphSpec` | `kind`, `size`, `label` |
| `GrowthPhase` | `n_nodes`, `minority_fraction`, `homophily` |
| `NetworkCondition` | `name`, `phases` |
| `ThresholdSpec` | `mode`, `value`, `distribution`, `resampling` |
| `SeedSpec` | `groups`, `count`, `fraction` |
| `GlobalCascadeRule` | `relative_size_cutoff` |
| `CascadeSpec` | `threshold`, `seeds`, `n_cascades`, `global_rule`, `record_trajectory` |
| `Experiment` | `run`, `initial_graph`, `conditions`, `cascade`, `m`, `zero_weight_fallback` |

```python
def validate_experiment(experiment: Experiment) -> None
def validate_pairing(conditions: tuple[NetworkCondition, ...]) -> None
```

`validate_experiment` acumula todos los errores en un `ConfigError`.
`validate_pairing` exige que dos condiciones con el mismo prefijo de fases tengan
parámetros idénticos en ese prefijo.

### `loader.py`

```python
def load_module(path: str | Path) -> ModuleType
def build_cells(path: str | Path) -> list[Cell]
```

Importa por ruta con `importlib.util.spec_from_file_location`, verifica el
contrato, expande el diseño y valida cada celda.

### `design.py`

```python
@dataclass(frozen=True)
class Cell:
    index: int
    cell_id: str
    params: Mapping[str, Any]
    experiment: Experiment
    kind: Literal["control", "intervention"]

def expand_cells(build_experiment, design: Mapping[str, Sequence]) -> list[Cell]
def make_cell_id(index: int, params: Mapping[str, Any]) -> str
```

`cell_id` se deriva de un hash estable de los parámetros ordenados, nunca de
`hash()` de Python. Una celda es `control` cuando la condición `intervenida` y la
`baseline` tienen fases idénticas; sirve como verificación negativa del pipeline.

### `snapshot.py`

```python
def write_config_snapshot(cell: Cell, source_path: Path, run_dir: Path) -> None
def resolved_payload(experiment: Experiment) -> dict[str, Any]
```

Copia el módulo fuente, escribe `config_source.py` y `resolved.json` en el run.

## Invariantes

- Ningún valor por defecto oculto: todo parámetro numérico aparece en el esquema.
- Una configuración inválida falla con la lista completa de problemas.
- Congelar la configuración no depende de releer el módulo fuente.

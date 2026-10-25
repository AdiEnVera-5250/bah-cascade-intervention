# analysis

**Fase:** 6.
**Estado:** sin implementar.

Solo lectura. Consume `networks.csv` y `cascades.csv` de un run y produce tablas
agregadas y figuras en `reports/<run_id>/`. Nunca regenera redes ni cascadas, y
ningún resultado de este paquete se escribe dentro del run original.

## Módulos

### `load.py`

```python
@dataclass(frozen=True)
class RunDataset:
    run_dir: Path
    metadata: dict[str, Any]
    networks: pd.DataFrame
    cascades: pd.DataFrame

def load_run(run_dir: Path) -> RunDataset
```

Valida que existan las columnas esperadas y que la versión de esquema del run sea
compatible. Si falta una columna, falla con un mensaje que nombra la columna y el
run.

### `aggregate.py`

```python
def summarize(cascades: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame
```

Una fila por combinación de `by` (por defecto `cell_id`, `condition`,
`seed_group`) con: `n`, `mean`, `median`, `sd`, `q1`, `q3`, `global_probability`,
para `size_rel`, `composition`, `reach_minority`, `reach_majority` y
`stopping_time`.

### `compare.py`

```python
def paired_differences(cascades: pd.DataFrame, condition_a: str,
                       condition_b: str, by: Sequence[str],
                       rng: np.random.Generator) -> pd.DataFrame
def bootstrap_ci(values: np.ndarray, statistic, n_resamples: int,
                 rng: np.random.Generator) -> tuple[float, float]
```

Empareja por `network_id` y compara `a - b`. Reporta diferencia media, mediana, IC
bootstrap y tamaño del efecto. El emparejamiento es válido porque las condiciones
de una réplica comparten los sorteos de la fase previa; `compare` no lo verifica,
solo lo asume documentado.

### `plots.py`

```python
def plot_cascade_size_distribution(dataset, out_dir) -> Path
def plot_global_probability(dataset, out_dir) -> Path
def plot_group_reach(dataset, out_dir) -> Path
def plot_mixing_by_homophily(dataset, out_dir) -> Path
```

Figuras previstas: distribución de tamaño por condición, probabilidad de cascada
global frente a umbral, alcanzabilidad por grupo, y mezcla de grupos frente a
homofilia.

### `report.py`

```python
def build_report(run_dir: Path, out_dir: Path) -> Path
```

Encadena `load_run`, `summarize`, `paired_differences` y las figuras; escribe
`summary_by_condition_seed_group.csv`, `paired_differences.csv` y `figures/`.

## Invariantes verificadas por tests

- `summarize` reproduce un cálculo manual con pandas puro.
- En una celda de control, la diferencia pareada `intervenida - baseline` es
  exactamente 0.
- `bootstrap_ci` es determinista dada la semilla.
- `load_run` rechaza un run con columnas faltantes.

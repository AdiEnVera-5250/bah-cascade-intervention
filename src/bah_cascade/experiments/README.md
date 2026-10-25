# experiments

**Fase:** 5 (runner y persistencia), Fase 4 (`benchmark.py`).
**Estado:** sin implementar.

Orquesta el Monte Carlo y es la única capa autorizada a escribir archivos. No
contiene reglas científicas: solo recorre celdas, réplicas, condiciones y cascadas,
y delega en `networks/` y `cascades/`.

## Bucle de ejecución

```
for cell in celdas:
    for replicate in 0..n_replicates-1:
        records = networks.conditions.grow_conditions(...)
        for condition, record in records:
            escribir fila en networks.csv
            thresholds = cascades.thresholds.make_thresholds(...)
            for seed_group in grupos:
                for k in 0..n_cascades-1:
                    semillas = cascades.seeds.sample_seed_nodes(...)
                    resultado = engine.run(semillas)
                    escribir fila en cascades.csv
```

Cada red acumula además las métricas de `networks.metrics.structural_metrics`.

## Módulos

### `runner.py`

```python
@dataclass(frozen=True)
class RunCounts:
    cells: int
    networks: int
    cascades: int

def describe(cells: Sequence[Cell]) -> RunCounts
def execute(cells: Sequence[Cell], run_dir: Path, resume: bool = False) -> None
```

`describe` es lo que alimenta `bah-cascade describe`: permite ver el costo antes de
ejecutar. `execute` es idempotente con `resume=True`: no reescribe filas ya
presentes y falla si la configuración resuelta no coincide con la del run.

### `persistence.py`

```python
class RunWriter:
    def write_network(self, row: Mapping[str, Any]) -> None
    def write_cascade(self, row: Mapping[str, Any]) -> None
    def write_trajectory(self, rows: Sequence[Mapping[str, Any]]) -> None
    def close(self) -> None

def read_run(run_dir: Path) -> RunDataset
```

Layout del run:

```
results/<name>__<timestamp>__<hash>/
  config_source.py
  resolved.json
  metadata.json
  networks.csv
  cascades.csv
  cascade_trajectory.csv     (opcional)
  thresholds/<network_id>.npy (opcional, per_node)
  graphs/<network_id>.npz      (opcional)
  logs/run.log
```

Reglas de determinismo: orden de filas fijo (celda, réplica, condición, grupo de
semilla, cascada), formato de flotantes `%.10g`, escritura incremental con cierre
explícito. `metadata.json` guarda versión del paquete, versiones de dependencias,
intérprete, plataforma, semilla maestra, fecha y hash de la configuración resuelta.

### `benchmark.py`

```python
def benchmark_scale(sizes: Sequence[int], m_values: Sequence[int],
                    n_cascades: int, out_path: Path) -> pd.DataFrame
```

Mide tiempo de generación por red y tiempo por cascada para distintos tamaños y
`m`, y escribe un CSV. No optimiza nada: solo mide. Sirve para validar N = 1000 y
decidir si conviene subir a 5000.

## Invariantes verificadas por tests

- Dos ejecuciones con la misma semilla producen CSV idénticos byte a byte.
- `describe` coincide con la cantidad de filas efectivamente escritas.
- `resume` no duplica filas ni reescribe un run con otra configuración.

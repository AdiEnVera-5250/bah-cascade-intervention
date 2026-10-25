# networks

**Fase:** 2 (crecimiento y métricas), Fase 3 (condiciones emparejadas).
**Estado:** sin implementar.

Construye redes no dirigidas que crecen por adhesión preferencial con homofilia.
Este paquete no simula cascadas ni escribe archivos.

## Módulos

### `initial.py`

```python
def build_initial_graph(spec: InitialGraphSpec, m: int, rng: np.random.Generator) -> nx.Graph
```

Crea el grafo semilla y le asigna grupos con la misma cuota exacta que usan las
fases. Tipos previstos: `complete` (defecto, `m+1` nodos), `star`, `custom`.
Elimina la necesidad de la regularización `ε` del boceto.

### `groups.py`

```python
def quota_schedule(n_nodes: int, minority_fraction: float, rng: np.random.Generator) -> np.ndarray
def quota_count(n_nodes: int, minority_fraction: float) -> int
```

Devuelve un array de grupos de longitud `n_nodes` con exactamente
`quota_count(...)` minorías, usando resto mayor para el redondeo y una permutación
con stream propio para el orden. Códigos: `0` minoría, `1` mayoría.

### `growth.py`

```python
def attachment_weights(degrees: np.ndarray, same_group: np.ndarray, homophily: float) -> np.ndarray
def attach_new_node(graph, node, group, m, homophily, rng) -> AttachReport
def grow_phases(initial_graph, phases, m, homophily_by_phase, rng_by_phase, zero_weight_fallback) -> NetworkRecord
```

Peso de un candidato: `k_i * h_{g,g_i}`, normalizado sobre los candidatos con peso
positivo. Selección sin reemplazo. `AttachReport` registra aristas logradas y si se
usó el fallback.

Casos límite explícitos:

- Suma de pesos cero → nodo sin aristas, `isolated_at_birth=True`
  (`zero_weight_fallback = "none"`) o muestreo uniforme entre todos los nodos
  (`"uniform"`).
- Menos candidatos que `m` → se crean las aristas posibles y se registra
  `edges_shortfall`.
- Sin auto-lazos ni aristas múltiples.

### `conditions.py`

```python
def grow_conditions(experiment, replicate: int, master_seed: int, cell_index: int) -> dict[str, NetworkRecord]
def check_pairing(records: dict[str, NetworkRecord]) -> None
```

Genera todas las condiciones de una réplica compartiendo las claves de RNG por
índice de fase (no por nombre de condición). Consecuencia: la condición `pre` es
isomorfa al subgrafo inducido por los nodos de la fase 0 de `intervenida` y de
`baseline`, y `intervenida` vs `baseline` difieren solo en los parámetros de la
fase 1.

`NetworkRecord` contiene: grafo, grupos, fase de nacimiento de cada nodo, semilla
de la fase, parámetros efectivos, fracción de minoría por fase y global, y flags
de fallback.

### `metrics.py`

```python
def structural_metrics(graph: nx.Graph, record: NetworkRecord) -> dict[str, float | int]
```

Columnas previstas: `n_nodes`, `n_edges`, `n_minority`, `n_majority`,
`minority_fraction_nodes`, `minority_fraction_arrivals_phase_*`, `n_isolated`,
`isolated_at_birth`, `n_components`, `giant_component_fraction`,
`cross_group_edge_fraction`, `within_minority_fraction`,
`within_majority_fraction`, `assortativity_group`, `modularity`, `mean_degree`,
`sd_degree`, `max_degree`, `clustering_mean`.

## Invariantes verificadas por tests

- `graph.number_of_nodes()` coincide con la suma de fases más la semilla.
- Cuota exacta: `(schedule == 0).sum() == quota_count(...)`.
- `h = 1` no produce aristas entre grupos; `h = 0` no produce aristas internas.
- `pre` isomorfo al subgrafo de fase 0 de las otras condiciones.
- Repetir la generación con la misma semilla y celda produce la misma red.

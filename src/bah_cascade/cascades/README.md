# cascades

**Fase:** 4.
**Estado:** sin implementar.

Cascadas de umbral sobre una red ya construida. No genera redes ni persiste nada:
recibe el grafo y devuelve resultados en memoria.

## Regla

Un nodo inactivo se activa si `vecinos_activos / grado >= φ_i`. Actualización
síncrona: todas las activaciones de una iteración usan el estado del inicio de esa
iteración. Los nodos aislados nunca se activan por contagio; solo si son semilla.
Terminación garantizada en a lo sumo `n_nodes` iteraciones.

## Módulos

### `thresholds.py`

```python
def make_thresholds(graph: nx.Graph, spec: ThresholdSpec, rng: np.random.Generator) -> np.ndarray
def threshold_summary(thresholds: np.ndarray) -> dict[str, float]
```

- `mode="homogeneous"`: vector constante igual a `value`.
- `mode="per_node"`: muestreo independiente por nodo desde `distribution`
  (previsto: uniforme `low..high`; extensible sin cambiar la interfaz).
- `resampling="per_network"`: un vector por red, reutilizado en todas sus cascadas.
- `resampling="per_cascade"`: vector nuevo por cascada, con semilla registrada.

`threshold_summary` produce `threshold_mean`, `threshold_sd`, `threshold_min`,
`threshold_max`, que se guardan junto a la red o a la cascada según el resorteo.

### `seeds.py`

```python
def sample_seed_nodes(graph, group: str, count: int | None, fraction: float | None,
                      rng: np.random.Generator) -> list[int]
```

Sin reemplazo, dentro del grupo pedido (`minority`, `majority`) o sobre toda la red
(`uniform`). Si el grupo tiene menos nodos que las semillas solicitadas se lanza
`CascadeError` indicando red, grupo y tamaños; no se ajusta el número en silencio.

### `engine.py`

```python
class ThresholdCascadeEngine:
    def __init__(self, graph: nx.Graph, thresholds: np.ndarray) -> None
    def run(self, seed_nodes: Sequence[int], cascade_id: str) -> CascadeResult
    def run_many(self, seed_sets: Sequence[Sequence[int]]) -> list[CascadeResult]
```

Construye una representación CSR una sola vez por red y actualiza contadores de
vecinos activos de forma incremental (`O(E)` por cascada, independiente del número
de iteraciones). Reutilizar el motor entre cascadas es obligatorio en el runner.

### `results.py`

```python
@dataclass(frozen=True)
class CascadeResult:
    seed_nodes: tuple[int, ...]
    seed_group: str
    size_abs: int
    size_rel: float
    active_minority: int
    active_majority: int
    reach_minority: float
    reach_majority: float
    composition: float
    overrepresentation: float
    is_global: bool
    stopping_time: int
    max_iterations_hit: bool
    trajectory: tuple[tuple[int, int, int], ...] | None

def to_row(result: CascadeResult, context: Mapping[str, Any]) -> dict[str, Any]
```

Definiciones: `composition = active_minority / size_abs`;
`overrepresentation = composition - minority_fraction_nodes`;
`reach_minority = active_minority / n_minority`; `is_global = size_rel >= cutoff`;
`stopping_time` = número de iteraciones con al menos una activación nueva.

## Invariantes verificadas por tests

- Igualdad exacta: `fracción == φ` activa.
- Nodo aislado no se activa si no es semilla.
- `φ = 0` activa a todos los nodos con al menos un vecino en la primera iteración.
- `φ = 1` solo propaga por vecindarios completamente activos.
- Suma de activaciones por grupo igual a `size_abs`.
- Misma red, mismas semillas, mismos umbrales → mismo resultado.

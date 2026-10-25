# bah_cascade

**Fase:** 1 (pendiente de autorización).
**Estado:** marcadores de paquete creados; sin lógica implementada.

Paquete principal del proyecto. La regla estructural es que la generación de datos
y su análisis no comparten estado: `networks/`, `cascades/` y `experiments/`
nunca leen archivos de resultados, y `analysis/` nunca genera redes ni cascadas.

## Flujo de datos

```
config/*.py (módulo de experimento)
        |
        v
experiments.runner  ->  networks.conditions  ->  cascades.engine
        |                                              |
        +------------------ CSV -----------------------+
                           |
                           v
                    analysis.report
```

## Módulos raíz

| Módulo | Responsabilidad | Fase |
|---|---|---|
| `errors.py` | Excepciones propias: `ConfigError`, `NetworkError`, `CascadeError` | 1 |
| `rng.py` | Derivación determinista de generadores desde una semilla maestra | 1 |
| `cli.py` | Punto de entrada: `validate`, `describe`, `run`, `analyze`, `benchmark` | 1 |

### `errors.py`

Jerarquía mínima, sin lógica:

- `ProjectError` — base.
- `ConfigError` — acumula una lista de mensajes de validación.
- `NetworkError` — invariantes de generación violadas.
- `CascadeError` — entrada inválida del motor de cascadas.

### `rng.py`

```python
STREAM: Final[dict[str, int]]

def derive_sequence(master_seed: int, *keys: int) -> np.random.SeedSequence
def derive_rng(master_seed: int, *keys: int) -> np.random.Generator
```

Reglas: nunca `seed + i`, nunca `hash()`; las claves son enteros de un registro
congelado; misma combinación produce siempre el mismo stream.

### `cli.py`

```python
def main(argv: list[str] | None = None) -> int
```

Subcomandos previstos: `validate`, `describe`, `run`, `analyze`, `benchmark`.
`describe` informa cantidad de celdas, redes y cascadas sin ejecutar nada.

## Subpaquetes

| Directorio | Responsabilidad |
|---|---|
| `config/` | Especificación y validación del experimento |
| `networks/` | Crecimiento, cuotas de grupo, condiciones emparejadas y métricas estructurales |
| `cascades/` | Umbrales, semillas y motor de cascadas |
| `experiments/` | Orquestación Monte Carlo, persistencia y benchmark |
| `analysis/` | Agregación, comparaciones y figuras (solo lectura) |

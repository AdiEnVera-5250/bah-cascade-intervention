# tests/unit

**Fase:** 2–6.
**Estado:** vacío.

Tests de una sola unidad, sin E/S de disco salvo `tmp_path`, y sin redes de más de
100 nodos.

## Cobertura prevista por archivo

| Archivo | Cubre |
|---|---|
| `test_rng.py` | Misma clave → mismo stream; claves distintas → streams distintos; sin dependencia del orden de llamadas |
| `test_config_schema.py` | Validaciones, errores acumulados, `validate_pairing` |
| `test_config_loader.py` | Contrato `DESIGN` + `build_experiment`, pureza, claves de parámetros |
| `test_design.py` | Expansión del producto cartesiano, `cell_id` estable, celdas de control |
| `test_groups.py` | Cuota exacta, resto mayor, permutación determinista, `p = 0` y `p = 1` |
| `test_growth.py` | Pesos, sin reemplazo, fallback, `edges_shortfall`, invariancia de semilla |
| `test_metrics.py` | Matriz de mezcla, modularidad, componentes, grados |
| `test_thresholds.py` | Homogéneo, por nodo, resorteo y resumen |
| `test_seeds.py` | Muestreo por grupo, sin reemplazo, grupo insuficiente |
| `test_engine.py` | Regla `>=`, síncrono, aislados, `φ = 0`, `φ = 1`, tiempo de parada |
| `test_results.py` | Composición, alcanzabilidad, sobre-representación, flag global |
| `test_aggregate.py` | Estadísticos contra cálculo manual |
| `test_compare.py` | Diferencia pareada, IC bootstrap determinista, celda de control |

# bah-cascade-intervention

Proyecto de investigación sobre cómo los mecanismos de crecimiento de red y las
intervenciones a nivel de grupo afectan la dinámica de cascadas en redes sociales.

Combina generación estocástica de redes con homofilia y cuotas de grupo,
simulación de cascadas de umbral, experimentos Monte Carlo y análisis estadístico
de los resultados.

## Estado

**Andamiaje creado. Fase 0 y Fase 1 pendientes de autorización.**

Todavía no hay código de modelo ni de simulación. Cada directorio contiene un
`README.md` con su responsabilidad, los módulos y funciones previstas, las
invariantes que debe respetar y la fase en la que se implementa. Ese archivo es la
fuente de verdad para recuperar contexto sin releer el código.

## Estructura

```
docs/          especificación del modelo, arquitectura y decisiones (ADR)
configs/       módulos .py que describen experimentos
src/           paquete bah_cascade
tests/         unitarios, integración y fixtures
results/       datasets generados (ignorados por git)
reports/       análisis y figuras derivadas (ignorados por git)
```

## Puesta en marcha

```powershell
uv sync --extra dev
uv run pytest
```

El intérprete de referencia es Python 3.14 (`.python-version`). El proyecto exige
`>=3.11`.

## Decisiones de diseño vigentes

Resumen operativo; el detalle y la justificación viven en `docs/`.

| Dimensión | Decisión |
|---|---|
| Umbral | Homogéneo global por defecto; vector por nodo opcional; resorteo `per_network` o `per_cascade` |
| Semillas | Número absoluto y/o fracción del grupo; muestreo sin reemplazo |
| Grupos | Cuota exacta por fase de llegada, orden barajado, método del resto mayor |
| Red inicial | Grafo semilla configurable; defecto completo de `m+1` nodos |
| Peso de adhesión cero | Nodo sin aristas, marcado `isolated_at_birth`; `zero_weight_fallback` configurable |
| Comparación | `pre`, `intervenida` y `baseline` emparejadas por réplica con sorteos compartidos |
| Cascada global | `size_rel >= cutoff` (defecto 0.5) |
| Configuración | Módulos Python con `DESIGN` y `build_experiment(params)` |
| Datos | CSV (gzip opcional) |
| Escala | N = 1000 (500 + 500), `m ∈ {1,2}`, con benchmark disponible |
| Dependencias | numpy, networkx, pandas, matplotlib; dev: pytest |

## Documentación

- `docs/README.md` — índice, decisiones y fase actual.
- `src/bah_cascade/README.md` — flujo de datos y mapa del paquete.
- `Monolith.py` — boceto original de referencia. No forma parte del paquete y no
  debe copiarse.

# reports

**Fase:** 6.
**Estado:** vacío.

Salidas de `bah-cascade analyze`. Todo el contenido está ignorado por git; solo
este archivo y el `.gitignore` se versionan.

## Layout

```
reports/<run_id>/
  summary_by_condition_seed_group.csv
  paired_differences.csv
  figures/
    cascade_size_distribution.png
    global_probability_by_threshold.png
    group_reach.png
    mixing_by_homophily.png
```

## Reglas

- Un reporte es siempre derivado: se puede borrar y regenerar desde `results/`.
- Ningún número se escribe a mano en un reporte.
- Cada figura debe poder rastrearse a una combinación de `cell_id`, `condition` y
  `seed_group`.

# tests/integration

**Fase:** 3–6.
**Estado:** vacío.

Prueban el pipeline completo con `configs/smoke.py`: N = 60, 3 réplicas, 5
cascadas. Deben correr en segundos.

## Pruebas previstas

| Archivo | Verifica |
|---|---|
| `test_paired_growth.py` | Para cada réplica: `pre` isomorfo al subgrafo inducido de fase 0 de `intervenida` y `baseline` |
| `test_run_contract.py` | Columnas, tipos y ausencia de nulos obligatorios en `networks.csv` y `cascades.csv` |
| `test_determinism.py` | Dos ejecuciones con la misma configuración → archivos idénticos byte a byte |
| `test_resume.py` | `--resume` no duplica filas; configuración distinta → error |
| `test_analysis.py` | `build_report` sobre el run de smoke produce las tablas y figuras esperadas |
| `test_control_cell.py` | En una celda de control, `intervenida - baseline` es exactamente 0 |

## Reglas

- Nunca se usan datasets reales ni rutas absolutas.
- Todo se escribe en `tmp_path`.
- Si un test de integración tarda más de ~10 s, el problema es el test.

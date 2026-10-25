# tests

**Fase:** 1 (infraestructura), 2–6 (cobertura por módulo).
**Estado:** sin tests.

`pytest` es el único runner. Comando de referencia:

```powershell
uv run pytest
```

## Organización

| Directorio | Contenido |
|---|---|
| `unit/` | Reglas del modelo, invariantes y cálculos aislados |
| `integration/` | Redes diminutas, simulaciones cortas y contrato de datos |
| `fixtures/` | Grafos y datasets construidos a mano, con resultado esperado |

Los tests se nombran `test_<modulo>.py` y replican la estructura de
`src/bah_cascade/`.

## Prioridades de cobertura

1. Cuota exacta y orden barajado determinista.
2. Invariantes de generación: sin auto-lazos, sin multiejes, grados, grupos.
3. Regla de adhesión: monotonía de la mezcla en `h`, casos `h = 0` y `h = 1`.
4. Emparejamiento: `pre` isomorfo al subgrafo de fase 0.
5. Regla de cascada: igualdad `>=`, aislados, `φ = 0`, `φ = 1`, terminación.
6. Métricas por grupo y cascada global.
7. Agregación y diferencias pareadas contra cálculo manual.
8. Determinismo extremo a extremo: dos runs → CSV idénticos byte a byte.
9. Validación de configuración: errores acumulados y claros.
10. `resume`: ni duplicados ni sobreescritura con configuración distinta.

## Reglas

- Nada de redes grandes: los tests usan N ≤ 100.
- Nada de tiempo real como criterio de aceptación.
- Toda semilla es explícita; no se usa el estado global de `numpy` ni `random`.
- Los tests no escriben fuera de `tmp_path`.

# configs

**Fase:** 7 (diseños definitivos); `smoke.py` se crea en Fase 1.
**Estado:** vacío.

Módulos Python que describen experimentos. No son scripts: no ejecutan nada al
importarse, solo exponen dos nombres.

## Contrato

```python
DESIGN: dict[str, tuple]                              # factores del diseño

def build_experiment(params: dict[str, float]) -> Experiment: ...
```

- `DESIGN = {}` significa una sola celda sin factores.
- Cada clave de `params` corresponde exactamente a una clave de `DESIGN`.
- `build_experiment` debe ser puro y sin efectos secundarios.
- Los módulos solo construyen dataclasses de `bah_cascade.config.schema`; no
  contienen bucles de simulación, ni lectura de archivos, ni aleatoriedad.

## Archivos previstos

| Archivo | Contenido | Fase |
|---|---|---|
| `smoke.py` | N = 60, 3 réplicas, 5 cascadas por celda, 1 umbral; corre en segundos | 1 |
| `calibration.py` | Barrido estructural sin cascadas: `m`, `h`, `p` → mezcla, componentes, grados | 7 |
| `intervention_main.py` | Diseño principal: `pre` / `intervenida` / `baseline`, N = 1000 (500 + 500), `m ∈ {1,2}`, `p_post ∈ {0.2, 0.3, 0.4}`, umbrales `{0.1, 0.2, 0.3}` | 7 |

`smoke.py` es también la configuración usada por los tests de integración y por la
prueba de determinismo byte a byte.

## Comandos

```powershell
bah-cascade validate configs/smoke.py
bah-cascade describe configs/intervention_main.py
bah-cascade run configs/smoke.py
```

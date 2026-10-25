# results

**Fase:** 5 (escritura), 6 (lectura).
**Estado:** vacío.

Datasets generados por `bah-cascade run`. Todo el contenido está ignorado por git;
solo este archivo y el `.gitignore` se versionan.

## Layout de un run

```
results/<name>__<timestamp>__<hash>/
  config_source.py             copia del módulo de configuración usado
  resolved.json                parámetros resueltos por celda
  metadata.json                versiones, semilla maestra, fecha, hash
  networks.csv                 una fila por red
  cascades.csv                 una fila por cascada
  cascade_trajectory.csv       opcional, una fila por iteración
  thresholds/<network_id>.npy  opcional, vectores por nodo
  graphs/<network_id>.npz      opcional, adyacencia y atributos
  logs/run.log
```

## Reglas

- Un run nunca se modifica a mano.
- Un run es reproducible a partir de `config_source.py` + `metadata.json`; si esos
  archivos faltan, el run no es válido para análisis.
- Borrar runs es seguro: se regeneran desde configuración y semilla.
- Los CSV usan orden de filas fijo y formato de flotantes `%.10g`.

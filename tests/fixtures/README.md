# tests/fixtures

**Fase:** 2–6.
**Estado:** vacío.

Grafos y datasets construidos a mano, pequeños y legibles, con su resultado
esperado calculado a lápiz. No se generan con el propio código del proyecto: si se
generaran así, el test no verificaría nada.

## Contenido previsto

| Fixture | Uso |
|---|---|
| `line_graph` | Propagación en cadena, un solo camino |
| `isolated_node` | Nodo sin vecinos que nunca se activa salvo como semilla |
| `two_cliques` | Activación con `φ = 1` dentro del clique |
| `exact_threshold` | Fracción de vecinos activos exactamente igual a `φ` |
| `star_graph` | Centro con grado alto y hojas con grado 1 |
| `two_group_graph` | Composición y alcanzabilidad por grupo |
| `cascade_cases.csv` | (red, φ, semillas) → tamaño, composición y tiempo esperados |

## Reglas

- Cada fixture documenta en un comentario o en este archivo por qué el resultado
  esperado es el que es.
- Si un fixture cambia, se actualiza el resultado esperado en el mismo cambio.
- Los CSV de fixtures sí se versionan (están fuera de las rutas ignoradas).

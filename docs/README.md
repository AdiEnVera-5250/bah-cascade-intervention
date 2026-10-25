# docs

**Fase:** 0 (pendiente de autorización).
**Estado:** directorio creado, contenido por escribir.

Documentación de referencia del proyecto. Todo lo que aquí se escriba debe poder
leerse sin abrir el código.

## Contenido previsto

| Archivo | Responsabilidad | Fase |
|---|---|---|
| `model.md` | Especificación formal: crecimiento, cuotas, homofilia, regla de cascada, casos límite y definición de cada métrica | 0 |
| `architecture.md` | Arquitectura de módulos, contratos de datos y flujo de ejecución | 0 |
| `decisions/` | Registros de decisión (ADR) con contexto y consecuencias | 0 |

## Convenciones

- Documentación en español; código, identificadores y nombres de columna en inglés.
- Cada afirmación científica debe indicar su parámetro configurable asociado.
- Las métricas se definen con fórmula explícita, no con descripciones ambiguas.
- Ningún parámetro numérico se documenta como constante fija: se indica dónde se
  configura.

## Decisiones pendientes de redactar como ADR

1. Cuota exacta por fase de llegada (no acumulada).
2. Regla de peso cero: nodo sin aristas en lugar de regularización `ε`.
3. Emparejamiento de condiciones por réplica con sorteos compartidos.
4. Umbral homogéneo por defecto y vector por nodo opcional.
5. Formato de configuración en módulos Python y congelado en el run.
6. Datos en CSV, sin Parquet.

## Fase actual

Fase 0 no iniciada. El andamiaje de directorios y el control de contexto están
listos; el siguiente paso autorizado será escribir `model.md`, `architecture.md` y
los ADR.

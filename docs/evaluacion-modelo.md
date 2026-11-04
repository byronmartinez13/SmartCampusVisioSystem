# Evaluar el conteo frente a personas

Los resultados visuales actuales no acreditan el objetivo de error máximo de ±2 personas ni detección de puestos utilizables. No se asignará una precisión inventada.

1. Usar videos representativos del laboratorio real: personas sentadas, filas del fondo, iluminación, oclusiones y distintos niveles de ocupación.
2. Descargar el JSON de cada análisis. `result.samples` identifica los fotogramas evaluados y sus conteos.
3. Revisar esos fotogramas del archivo original y contar las personas manualmente. Conviene que una segunda persona revise discrepancias. No usar las predicciones del modelo como etiquetas humanas.
4. Crear un JSON como el siguiente, sustituyendo el identificador y los conteos por observaciones reales. Los números siguientes son solo un ejemplo de formato, no etiquetas del proyecto:

```json
{
  "analysis_id": "UUID-del-analisis-exportado",
  "samples": [
    {"frame": 0, "people": 12},
    {"frame": 15, "people": 13}
  ]
}
```

5. Ejecutar desde la raíz:

```powershell
.\services\vision\.venv\Scripts\python.exe services/vision/evaluate_counts.py analisis.json anotaciones.json --output tmp/evaluacion-conteos.json
```

El evaluador informa error absoluto medio y máximo, fotogramas fuera de ±2 y el modelo usado. Rechaza fotogramas inexistentes/duplicados, etiquetas vacías e identificadores distintos. Un resultado favorable solo corresponde a los fotogramas anotados; no garantiza el comportamiento en otras aulas.

La clase `tv` detecta monitores/televisores, no estaciones completas ni puestos utilizables. RF-03 requiere definir físicamente qué constituye un puesto, etiquetar ejemplos y evaluar un modelo apropiado; contar monitores no completa esa validación. La capacidad humana validada se mantiene como referencia de ocupación y asignaciones.

La mejora de fluidez/GPU queda aplazada por decisión del grupo. Registrar aparte hardware, resolución, modelo, tiempo de carga inicial y latencia por muestra para comparar equipos sin confundir la fluidez del video con precisión de detección.

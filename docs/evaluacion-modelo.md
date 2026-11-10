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

Se optimizó el muestreo de cámara eliminando la espera fija de un segundo, sin añadir GPU. Registrar aparte hardware, resolución, modelo, tiempo de carga inicial y latencia por muestra para comparar equipos sin confundir fluidez del video con precisión de detección.

## Comparación inicial del candidato Roboflow (10 de noviembre de 2026)

Dataset exportado: 23 imágenes de entrenamiento, siete de validación y siete de prueba. Entrenamiento contiene 323 anotaciones de monitores y 19 de personas; test contiene 40 de monitores y 42 de personas (no personas únicas). No se encontraron archivos idénticos entre splits; eso no descarta tomas casi idénticas ni prueba independencia de escenas.

Se compararon YOLO11n original y el candidato `campus-entrenado.pt`, ambos con confianza 0,50, entrada 640 y CPU. Para el original se mapeó `tv` a monitor. Respecto a las etiquetas proporcionadas, el MAE de conteo de personas fue 1,00 con el original y 5,57 con el candidato; el máximo error fue 2 y 7, respectivamente. En monitores el MAE fue 3,00 y 4,71. Se revisaron siete láminas de comparación. El candidato omitió numerosas personas y algunas anotaciones de monitor incluyen partes del puesto; conviene revisar el etiquetado antes de reentrenar.

Se mantiene el modelo original en AWS. La muestra pequeña del mismo laboratorio y las etiquetas no auditadas exhaustivamente no certifican precisión general. Estos datos de test ya se han utilizado para decidir entre modelos: no deben reutilizarse como test intocado durante futuros ajustes. Pesos, dataset y láminas permanecen fuera de Git; el informe local está en `tmp/comparacion-modelos/`.

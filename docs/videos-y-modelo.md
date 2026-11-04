# Videos de referencia y evolución del detector

## Requisitos confirmados por el usuario

La implementación debe utilizar Django, Django REST Framework, AWS, al menos un microservicio y una librería de inteligencia artificial. El curso de Amazon con certificación es responsabilidad académica del estudiante y no se implementa dentro del sistema.

Se mantiene la arquitectura del documento: backend Django/DRF, PostgreSQL y microservicio de visión con FastAPI, YOLO y OpenCV. React y TypeScript se proponen para la interfaz sin sustituir el backend requerido. AWS corresponde al destino de despliegue; el desarrollo comienza localmente.

## Inspección de archivos

Los originales permanecen en la carpeta `SmartCampusVisionV3/data/videos` indicada por el usuario; no se modificaron ni se copiaron al repositorio.

| Archivo | Duración aproximada | Resolución | FPS | Fotogramas informados |
| --- | --- | --- | --- | --- |
| clase0.mp4 | 57,30 s | 478 × 850 | 30 | 1719 |
| clase1.mp4 | 5,17 s | 1536 × 672 | 24 | 124 |
| clase2.mp4 | 5,17 s | 1536 × 672 | 24 | 124 |
| clase3.mp4 | 5,17 s | 2944 × 1248 | 24 | 124 |

Método: OpenCV abrió cada archivo y decodificó fotogramas al inicio, aproximadamente a la mitad y al 90 % del recorrido. Se inspeccionó visualmente el fotograma central de cada video. Esto verifica lectura de muestras, no la integridad de todos los fotogramas ni la precisión de un detector.

Metadatos y posiciones exactas: `referencias/videos-inventario.json`.

Observaciones:

- El fotograma revisado de `clase0` muestra un laboratorio en formato vertical y solo una parte del espacio.
- Los fotogramas revisados de `clase1`, `clase2` y `clase3` muestran laboratorios y la marca visible “MINIMAX | Hailuo AI”. Esto sugiere material generado con IA; su procedencia no está confirmada por el usuario.
- Estos videos sirven para probar carga, decodificación, procesamiento y presentación. No constituyen por sí solos evidencia de precisión en aulas reales.
- No se ejecutó todavía YOLO ni se asignaron conteos manuales de referencia.

## Contrato previsto para poder cambiar el modelo

El grupo entrenará un modelo para la entrega final. La aplicación debe permitir reemplazarlo sin modificar las pantallas ni las reglas académicas:

1. Configurar externamente la ubicación de los pesos, la versión del modelo, las clases y el umbral de confianza.
2. Definir una interfaz de detector con entrada de fotograma y salida de cajas, clase y confianza.
3. Normalizar las clases del modelo a conceptos del dominio: persona y puesto. No depender de identificadores numéricos de clase dispersos por el código.
4. Registrar junto al análisis la versión del modelo, sus parámetros y la fuente de video, para reproducir los resultados.
5. Mantener la inferencia separada de los cálculos de ocupación, la validación humana y las recomendaciones.
6. Si faltan pesos o clases requeridas, comunicar el problema; no sustituirlo por conteos inventados.

El “puesto de trabajo” requiere una definición de etiquetado acordada: una estación utilizable, no la suma automática de silla, monitor y mesa. La capacidad validada por una persona seguirá siendo un dato separado de la estimación visual.

## Validación prevista

- Anotar fotogramas de referencia con conteos manuales de personas y puestos, indicando qué hacer con objetos parcialmente visibles.
- Reservar videos/escenas para evaluación que no se utilicen en entrenamiento.
- Evaluar el límite de ±2 personas del PDF sobre los fotogramas de referencia, conservando errores individuales y casos que incumplen.
- Medir por separado el conteo de puestos; el documento no establece para este una tolerancia numérica equivalente.
- No sumar personas detectadas entre fotogramas como si fueran personas distintas.
- Registrar hardware, modelo, resolución de inferencia y tiempo de procesamiento al medir rendimiento.

La precisión queda pendiente de evaluación. El entrenamiento final y su calidad no están acreditados por la inspección de estos archivos.

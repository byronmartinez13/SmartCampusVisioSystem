# Hito 3 — Análisis de video

## Flujo implementado

1. Un administrador selecciona un aula activa, curso opcional, actividad, confianza y video.
2. Django valida extensión, cabecera y tamaño, conserva el archivo privado y una instantánea de la capacidad validada.
3. `run_video_worker` envía el trabajo por HTTP al microservicio. UUID remoto e inserción idempotente evitan duplicarlo ante una respuesta perdida.
4. FastAPI comprueba que OpenCV decodifica el video y lo coloca en su cola persistente. Un trabajador carga YOLO una vez y evalúa aproximadamente dos fotogramas por segundo en CPU.
5. El navegador consulta el estado persistido por Django. Puede abandonar la página, regresar, cancelar o reintentar tras un fallo.
6. Se muestran máximos y promedio, fotogramas evaluados, tiempo, modelo, imagen anotada y tabla temporal. El JSON descargable conserva metadatos y cajas del fotograma máximo.
7. **Guardar resultado** crea una sola entrada de actividad y, si el máximo supera la capacidad validada, una alerta. Repetir la solicitud no duplica registros. La página del aula y el dashboard utilizan ese resumen.

Las nuevas cuentas siguen siendo de consulta. Las rutas de modificación requieren rol administrador y CSRF. El microservicio no conoce usuarios; Django controla el acceso y utiliza una clave exclusivamente interna. Los videos no se publican mediante una ruta estática.

## Responsabilidades

- `backend/video_analysis/models.py`: persistencia del contexto y resultado.
- `serializers.py`: validación de entrada y representación pública.
- `client.py`: adaptador HTTP interno.
- `services.py`: sincronización y guardado transaccional.
- `views.py`: endpoints REST y autorización.
- `services/vision/app/detector.py`: contrato de detección y adaptador YOLO.
- `processor.py`: decodificación, muestreo, agregación y vista anotada.
- `store.py`: cola SQLite y recuperación.
- `frontend/src/VideoAnalysis.tsx`: configuración, progreso, consulta y acciones.

## Límites explícitos

- MP4/AVI, hasta 250 MiB, 10 minutos, área de imagen máxima 4096×4096. La validación de decodificación ocurre en el microservicio: una cabecera válida no garantiza un archivo íntegro.
- Hasta diez trabajos pendientes. Un único sincronizador Django y una sola instancia del microservicio. Tres errores consecutivos de comunicación marcan el trabajo como fallido; se puede reintentar. La cancelación pendiente sigue intentando contactar al servicio hasta confirmarse.
- La ocupación es `máximo de personas detectadas / capacidad validada al cargar × 100`. Sin capacidad o con capacidad cero no se calcula porcentaje. Las sillas detectadas no reemplazan la capacidad validada.
- Los máximos de personas y sillas pueden ocurrir en distintos fotogramas. No se suman detecciones repetidas para presentar personas únicas.
- La confianza del modelo no es una métrica de precisión. No se ha validado el error objetivo frente a anotaciones humanas. Los fotogramas no muestreados pueden contener eventos que el detector no capture.
- No hay eliminación automática de videos ni política de retención todavía. Los archivos permanecen privados en disco local. Antes de AWS se necesita almacenamiento privado, límites en proxy de subida, retención, observabilidad, PostgreSQL y cola distribuida si se escala.
- El frontend tiene subida con estado de espera; la barra posterior representa fotogramas evaluados, no bytes de transferencia.
- Continúan pendientes análisis en vivo, gestión de alertas, recomendaciones/horarios, reportes PDF y despliegue AWS. Este hito no certifica el sistema completo para producción.

## Evidencia con videos aportados

**Actualización de referencia visual:** los nuevos análisis usan monitores (`tv`, semántica `monitors`) en lugar de sillas. Se mantienen los resultados históricos con su semántica original. La evidencia de esta configuración se guarda separadamente en `vision-validation-monitors.json`. La tabla siguiente conserva la ejecución inicial con sillas.

Los monitores ayudan a revisar el inventario visual de un laboratorio, pero no acreditan que los equipos estén utilizables ni que cada pantalla corresponda a un puesto. No se calcula disponibilidad restando monitores y personas de máximos de fotogramas distintos. La capacidad validada sigue siendo la referencia para ocupación y futuras estimaciones de disponibilidad; la asignación a puestos concretos requerirá correspondencia espacial y validación.

Ejecución HTTP local del 20 de octubre de 2026, YOLO11n general, confianza 0,5, entrada del modelo 640, CPU:

| Video | Fotogramas evaluados | Máximo de personas | Máximo de sillas | Procesamiento |
|---|---:|---:|---:|---:|
| clase0.mp4 | 115 | 6 | 2 | 20,36 s |
| clase1.mp4 | 11 | 11 | 4 | 1,72 s |
| clase2.mp4 | 11 | 13 | 4 | 1,67 s |
| clase3.mp4 | 11 | 12 | 2 | 3,72 s |

Los tiempos excluyen subida y carga inicial del modelo. Los resultados detallados, hash de pesos y muestras están en `vision-validation.json`. Los conteos son salidas del detector, **no conteos manuales verdaderos**. Los videos 1–3 muestran marca Hailuo/Minimax y no sustituyen una evaluación con grabaciones reales del entorno.

## Verificación

```powershell
.\.venv\Scripts\python.exe backend/manage.py test accounts campus video_analysis
cd services/vision
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

En `frontend`: `npm.cmd run build` y `npx.cmd playwright test`.

Resultados: 42 pruebas Django, 6 del microservicio y 7 de navegador aprobadas; compilación frontend correcta.

Playwright inicia una base Django aislada, almacenamiento de pruebas, microservicio en 8003 y frontend en 5174. El test de video procesa un MP4 negro de tres fotogramas con el modelo real: verifica carga, procesamiento, persistencia al recargar, guardado y descarga. Esa prueba demuestra integración, no precisión del detector. Los cuatro videos originales se prueban por separado mediante `validate_samples.py`.

## Modelo del grupo

La ruta y clases del modelo se configuran por variables de entorno. Para sustituir los pesos hay que entrenar y separar conjuntos de entrenamiento/validación/prueba, documentar las clases, medir error absoluto por fotograma y evaluar casos de oclusión y aulas vacías. No cambiar `chairs` por `workstations` hasta que las etiquetas del modelo representen puestos.

Referencias de implementación: [predicción Ultralytics](https://docs.ultralytics.com/modes/predict/), [YOLO11](https://docs.ultralytics.com/models/yolo11/) y [subida de archivos en FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/).

# Hito 7 - Cámara local

Una cámara integrada o USB accesible al navegador. Entrada en Análisis > Abrir cámara, o `/analisis/en-vivo`. Requiere rol administrador, permiso de cámara, localhost o HTTPS y microservicio de visión activo en el puerto 8002. No requiere el trabajador Django de videos para las sesiones en vivo.

## Flujo

Seleccionar aula, actividad y umbral; iniciar cámara; consultar video local y última muestra anotada; detener; abrir resultado y guardar resumen. El resumen usa el máximo de personas y crea una alerta si supera la capacidad validada al iniciar. El historial distingue cámara de video y permite filtrar el origen; PDF y JSON usan el resultado persistido.

Se envía un JPEG por solicitud al backend y luego al microservicio con clave interna. Los conteos provienen del detector del servidor. No se aceptan conteos calculados por el cliente. El navegador espera cada respuesta y un segundo antes de la siguiente captura: no se garantiza una frecuencia fija ni video continuo anotado.

Los fotogramas se procesan en memoria y no se guardan. El resultado conserva conteos, tiempos, semántica del detector y modelo; no conserva imágenes del máximo. La vista local muestra el video de cámara y, separadamente, la última muestra analizada con retraso. Al detener o salir se liberan los tracks de cámara. La salida de página intenta cerrar la sesión; si falla la conexión o se cierra abruptamente el navegador, el registro puede quedar procesando. No recibe muestras después de diez minutos y puede cancelarse desde el detalle. No se envía audio.

## Límites

- Una cámara por sesión, máximo diez minutos o mil muestras. No incorpora RTSP/IP, fusión de cámaras, seguimiento de identidades ni eliminación de duplicados.
- Las imágenes JPEG se limitan a 2 MB y 1920 píxeles por lado en el servicio; el navegador solicita hasta 1280 x 720.
- Capacidad histórica al iniciar; los monitores detectados no acreditan puestos utilizables.
- La ocupación de la última muestra puede diferir del máximo guardado. La confianza no equivale a precisión, y las oclusiones pueden causar subconteo.
- Primera versión local en CPU: el servicio mantiene un detector para cámara y otro para videos; no se garantiza rendimiento si ambos se usan simultáneamente. El endpoint de cámara rechaza inferencias simultáneas con 429.
- Si hay error de cámara o servicio, se detiene el muestreo y se permite cerrar la sesión conservando muestras previas.
- Las sesiones solo pueden recibir muestras o detenerse desde su creador administrador; la consulta de resultados conserva los permisos generales existentes.

## Persistencia y concurrencia

Migración `video_analysis/0002`: origen `video` por defecto para registros anteriores. Sesiones de cámara reutilizan el contrato de resultado y no se despachan al trabajador de videos. Las escrituras comparan estado y fecha de actualización para rechazar muestras simultáneas o llegadas después de detener. La decisión de guardar resumen conserva la idempotencia existente.

## Ejecución

Además de Django y Vite, desde la raíz:

```powershell
.\services\vision\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/vision --host 127.0.0.1 --port 8002
```

La cámara física requiere una prueba manual con permiso del navegador y conteos humanos en el aula. Las pruebas automáticas usan cámara simulada, no activan la cámara del usuario.

## Verificación realizada

- Suite Django: 65 pruebas aprobadas durante la integración, más una prueba posterior de muestra en vuelo contra sesión detenida; las cuatro pruebas específicas de cámara aprobadas.
- Ocho pruebas del microservicio aprobadas, incluidas autenticación y validación JPEG para cámara.
- Compilación TypeScript/Vite correcta.
- Playwright aprobado con cámara sintética de Chromium y detector YOLO real: inicio, primera muestra, detención, liberación de tracks y consulta del resultado. No acredita precisión sobre personas reales.
- Vista de escritorio inspeccionada. La primera carga del detector tardó aproximadamente 27 segundos en el ensayo aprobado; el cliente interno admite hasta 120 segundos e informa que está preparando el modelo.

# Hito 4: historial, alertas y disponibilidad estimada

## Funcionalidad

- `/historial`: filtros por rango de fechas, aula (incluidas inactivas), actividad y estado de procesamiento; filtros persistidos en la URL, limpieza, paginación de 20 registros, enlace a resultados y descarga JSON.
- `/alertas`: filtros Todas/Nuevas/En revisión/Resueltas; acceso al análisis origen; cambio de estado por administrador; registro de actor, fecha y estado anterior/nuevo. Se puede reabrir una alerta. Repetir el mismo estado no duplica eventos.
- Dashboard: cuenta las alertas no resueltas, incluidas las que están en revisión.
- Disponibilidad en historial y detalle: `max(0, capacidad_snapshot - people_max)`. Sin capacidad validada al cargar o sin resultado completado se muestra no disponible. No se convierte el conteo de monitores en capacidad.

Las alertas se crean cuando se guarda el resumen de un análisis que supera la capacidad validada. Resolverlas registra una revisión administrativa; no modifica el video ni prueba que haya cambiado la ocupación del aula. Los registros antiguos sin video asociado se muestran con una explicación y sin enlace ficticio.

## API y permisos

- `GET /api/analysis-history/`: respuesta paginada, con `classroom`, `date_from`, `date_to`, `activity`, `status` y `page`. Fechas interpretadas en la zona horaria configurada (`America/Guayaquil`). Se rechazan rangos invertidos.
- `GET /api/alerts/`: respuesta paginada, filtro `status=new|review|resolved`.
- `POST /api/alerts/{id}/change-status/`: cuerpo `{"status":"review"}` (también `new` o `resolved`), autenticación, CSRF y rol administrador.
- Lectura disponible a los roles autenticados; modificación restringida a administradores.
- Migración `campus/0003`: conserva `resolved` y agrega estado de revisión, último actor/fecha y eventos de auditoría. Las alertas resueltas existentes permanecen resueltas.

## Verificación realizada

- 46 pruebas Django aprobadas, incluyendo filtros, paginación, permisos, historial de cambios, idempotencia del cambio y contador del dashboard.
- Dos recorridos Playwright aprobados: alertas/historial y carga/procesamiento/guardado de video real con YOLO.
- Compilación TypeScript/Vite correcta; capturas de escritorio y móvil revisadas.
- Las alertas sintéticas de navegador se crean exclusivamente en `config.e2e`, nunca en la base local del usuario.

## Pendientes de otras etapas

Reportes PDF, análisis en vivo, asignación y horarios, entrenamiento/evaluación final del modelo y AWS. El historial ofrece JSON; no presenta un botón PDF que no funcione. La disponibilidad mostrada es una estimación histórica, no puestos específicos libres ni información en tiempo real. PostgreSQL y despliegue aún requieren validación.
# Eliminación de análisis

Los administradores pueden eliminar definitivamente un análisis terminado desde Reportes, Historial o el detalle. La confirmación explica que se retiran el análisis, el archivo cargado, la copia del servicio de visión, la vista previa, el resumen y las alertas asociadas. No se permite eliminar mientras esté en cola, procesando o cancelándose. Al quitar el resumen también se actualizan dashboard y actividad del aula. Los PDF y videos ya descargados en otros equipos no se borran. Se conserva únicamente un evento administrativo de eliminación, sin copiar los resultados ni el video.

Si el servicio de visión no responde o aún procesa el video, el registro se conserva y se muestra un error para reintentar. No se añade borrado masivo ni se ejecuta limpieza automática sobre datos existentes.

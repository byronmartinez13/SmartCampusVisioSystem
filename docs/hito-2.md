# Hito 2: aulas y datos académicos

## Funcionalidad disponible

- Aulas y laboratorios: crear, consultar, buscar, filtrar por tipo/estado, editar y desactivar.
- Información del espacio: ubicación, capacidad declarada, equipamiento, referencia de cámara y disponibilidad semanal.
- Validación manual de capacidad: número de puestos, observación, responsable y fecha. Historial persistente de validaciones.
- Docentes y asignaturas: crear, consultar, buscar, editar y desactivar.
- Cursos: código, nombre, asignatura, docente, matrícula, equipamiento requerido y franjas semanales; creación, edición, consulta y desactivación.
- Conflictos de docente: impedir cursos activos superpuestos para el mismo docente. Los intervalos contiguos son válidos.
- Dashboard: el contador de aulas activas responde a altas y cambios de estado.

Los datos académicos son simulados. Las cámaras se registran únicamente como referencias; no se afirma que estén conectadas ni se procesan videos en este hito.

## Reglas y consistencia

- Solo administradores pueden escribir. Coordinadores y usuarios de consulta pueden leer; la API valida permisos, incluso si se envían peticiones fuera de la interfaz.
- Matrícula y capacidades: enteros entre 0 y 10 000. La capacidad declarada puede quedar sin definir.
- Capacidad validada: solo se modifica mediante su acción específica, que registra la evidencia. Cambiar capacidad declarada, tipo de espacio o equipamiento invalida la validación vigente y conserva el historial.
- Códigos, correos y nombres de aulas: unicidad sin distinguir mayúsculas, respaldada por restricciones de base de datos.
- Franjas: lunes a domingo, hora final posterior a inicial en el mismo día y sin superposición dentro de un registro.
- Curso activo: requiere docente y asignatura activos.
- No se puede desactivar un docente/asignatura con cursos activos asociados.
- Reactivar un curso o cambiar docente/franjas vuelve a comprobar los conflictos.
- Guardados relacionados dentro de transacciones. Un conflicto conserva los datos anteriores.
- No se exponen borrados definitivos; se usa estado activo/inactivo.
- Sin franjas significa disponibilidad/horario pendiente de configurar, no disponibilidad ilimitada.

## Recorrido recomendado

1. Iniciar sesión con una cuenta administradora.
2. Aulas → Nueva Aula/Laboratorio → completar datos y disponibilidad → Guardar.
3. En el detalle, registrar puestos comprobados y observación → Confirmar validación.
4. Datos académicos → Docentes → registrar docente.
5. Asignaturas → registrar asignatura.
6. Cursos → Nuevo curso → seleccionar referencias y registrar matrícula y franjas.

## Cuenta administradora local

Para una cuenta ya registrada:

```powershell
.\.venv\Scripts\python.exe backend/manage.py set_role correo@ejemplo.edu admin
```

Este comando requiere acceso local al proyecto. No expone elevación de privilegios mediante registro o edición pública. No concede acceso `is_staff` al administrador de Django.

Si se creó una cuenta sin contraseña inicial, usar recuperación para establecerla. En desarrollo los enlaces están en `backend/local-mail/`, duran una hora y solo se usan una vez. No hay contraseña por defecto.

## API añadida

| Recurso | Operaciones |
| --- | --- |
| `/api/classrooms/` | GET y POST; búsqueda `search`, filtros `kind` y `active` |
| `/api/classrooms/{id}/` | GET, PUT y PATCH |
| `/api/classrooms/{id}/validate-capacity/` | POST `{value, note}`; administrador |
| `/api/classrooms/{id}/validations/` | GET historial manual |
| `/api/classrooms/{id}/activity/` | GET hasta 20 resúmenes reales de análisis |
| `/api/teachers/` | GET y POST; búsqueda y filtro `active` |
| `/api/subjects/` | GET y POST; búsqueda y filtro `active` |
| `/api/courses/` | GET y POST; búsqueda y filtro `active` |
| `/api/{teachers,subjects,courses}/{id}/` | GET, PUT y PATCH |

Las colecciones están orientadas al conjunto reducido del prototipo; no incluyen todavía paginación.

## Validación y límites

Resultado: **34 pruebas backend y 6 recorridos Chromium aprobados**, compilación TypeScript/Vite correcta y migraciones sincronizadas. Se aplicó la migración del hito a la base local.

Las pruebas incluyen permisos/CSRF, persistencia, duplicados, matrícula inválida, intervalos, actualización atómica, conflictos, reactivación y validación de capacidad.
Los recorridos Chromium incluyen creación/edición/filtrado de aulas, validación manual, catálogos, cursos, conflicto de docente y denegación a consulta. Se revisaron capturas de escritorio y móvil.

Se continúa usando SQLite local. La lógica utiliza transacciones y bloqueos de fila para PostgreSQL, pero no se ha evaluado concurrencia con PostgreSQL en este equipo.

No están implementados todavía la asignación de aula a cursos, sus conflictos de espacio, las reglas/recomendaciones, los reportes PDF ni el procesamiento de video. El historial de validaciones manuales no reemplaza el historial futuro de análisis y decisiones.

## Referencias técnicas

- [ViewSets y acciones de Django REST Framework](https://www.django-rest-framework.org/api-guide/viewsets/).
- [Restricciones de modelos de Django](https://docs.djangoproject.com/en/5.2/ref/models/constraints/).

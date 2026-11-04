# Hito 5 — Asignación y horarios

## Flujo disponible

1. Configurar un aula activa con capacidad validada, equipamiento y disponibilidad semanal.
2. Configurar docente, asignatura y curso activos, matrícula positiva y franjas del curso.
3. Abrir **Horarios → Consultar alternativas**, seleccionar curso, período y preferencia opcional de aula/laboratorio.
4. El motor muestra alternativas compatibles, motivos y espacios excluidos con sus causas. La primera opción prioriza el tipo preferido y después el menor número de puestos sobrantes. No es un optimizador global.
5. Crear una propuesta pendiente. Esto **no reserva** el aula.
6. Revisar, aceptar (con opción de cambiar aula y franjas) o rechazar. Se requiere motivo y una confirmación explícita con el detalle final.
7. Al aceptar se validan otra vez las condiciones. La asignación aparece en el calendario semanal. Se puede cancelar, con motivo y confirmación, conservando la auditoría.

Los datos y porcentajes del prototipo no se copian. El calendario muestra ocupación **planificada**: matrícula / capacidad validada al aceptar. No representa ocupación medida por video. Las celdas son enlaces al detalle de la asignación y se pueden recorrer horizontalmente en pantallas pequeñas.

## Reglas implementadas

Restricciones obligatorias:

- Curso, docente, asignatura y aula activos.
- Matrícula positiva y capacidad validada suficiente; la capacidad declarada o los monitores detectados no la sustituyen.
- Equipamiento requerido contenido en el equipamiento registrado del aula.
- Todas las sesiones que ocurren en el período están cubiertas por disponibilidad explícita. Sin franjas de disponibilidad, el aula se excluye. Franjas disponibles contiguas se pueden combinar.
- Sin superposición de aula, docente ni del mismo curso con asignaciones aceptadas que coincidan en fechas efectivas. Una clase que termina a las 10:00 y otra que comienza a las 10:00 no se superponen.
- Período inclusivo de como máximo 366 días; al menos una sesión dentro de él. Las franjas no cruzan medianoche y usan minutos completos.

Preferencia flexible persistida por propuesta: priorizar aulas o laboratorios. Nunca permite saltar una restricción obligatoria. Los requisitos de equipamiento, matrícula, capacidad y disponibilidad se administran en los catálogos existentes. Esta entrega no incorpora todavía un editor arbitrario de reglas globales, pesos o excepciones.

Las franjas modificadas al aceptar pertenecen a esa asignación y período; no sobrescriben las franjas base del curso. Los cruces se comparan con asignaciones aceptadas. La validación previa del catálogo de cursos también sigue impidiendo cruces entre franjas base de cursos activos de un mismo docente.

## Integridad y auditoría

- La propuesta conserva instantánea del curso, docente, matrícula, requisitos, franjas base y capacidad.
- Si los datos del curso cambian mientras la propuesta está pendiente, no se acepta silenciosamente: se debe rechazar y generar una nueva.
- Cada decisión guarda actor, fecha, motivo y estados de aula/franjas/capacidad antes y después.
- Una propuesta ya resuelta rechaza una segunda decisión incompatible.
- Las decisiones y los cambios de catálogos comparten un bloqueo transaccional mediante una fila de control. La adquisición usa UPDATE antes de las lecturas de validación, también en SQLite.
- Cambios de catálogos que invaliden una asignación con sesiones pendientes se revierten. Se informa qué asignación cancelar antes de editar.
- Administradores y coordinadores pueden crear y resolver propuestas. Los demás usuarios autenticados solo consultan. Este permiso específico no amplía sus permisos para editar catálogos.

## Rutas

- Interfaz: /horarios, /horarios/nueva, /horarios/propuestas y /horarios/propuestas/:id.
- GET /api/assignments/alternatives/: consulta por curso, fechas y preferencia.
- POST /api/assignments/: crea propuesta compatible pendiente; curso, fechas, aula opcional y preferencia. La API admite franjas explícitas validadas.
- GET /api/assignments/: paginación de 20 propuestas y filtro de estado.
- GET /api/assignments/{id}/: contexto y decisiones.
- POST /api/assignments/{id}/decision/: acción accept, reject o cancel, motivo y opcionalmente aula/franjas nuevas al aceptar.
- GET /api/assignments/calendar/: aula y fecha; normaliza al lunes y devuelve las sesiones de esa semana.

Persistencia: migración campus/0004. No se crean cursos, aulas ni asignaciones de demostración en la base local del usuario.

## Verificación realizada

- 58 pruebas Django aprobadas, incluidas 12 nuevas de asignación.
- Capacidad desconocida/insuficiente, equipamiento, disponibilidad, preferencias, ausencia de sesiones, fechas y franjas inválidas.
- Conflicto de aula/docente, períodos separados y horarios contiguos.
- Aceptación modificada, auditoría, rechazo, cancelación, decisión duplicada, propuesta desactualizada, protección de catálogos y roles.
- Recorrido Playwright: crear datos por API, consultar alternativas, crear propuesta, modificar franja, confirmar, recargar, verificar porcentaje calculado en calendario, revisar móvil y cancelar.
- Ensayo con dos conexiones concurrentes sobre una base SQLite temporal: exactamente una aceptación, un conflicto y un evento de auditoría.
- Compilación TypeScript/Vite correcta; capturas de escritorio y móvil revisadas.

## Límites pendientes

La ejecución con PostgreSQL y carga concurrente de producción no se ha probado. No se manejan todavía feriados, semanas de excepción, períodos lectivos institucionales ni optimización conjunta de todos los cursos. El mapa de ocupación **medida** por video sigue pendiente; no debe confundirse con esta planificación. Continúan pendientes reportes PDF, análisis en vivo, editor general de reglas/configuración, entrenamiento/evaluación final del modelo y AWS.

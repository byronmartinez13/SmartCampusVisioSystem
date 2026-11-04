# Alcance y plan de verificación

## Fuentes y prioridad

Solicitud del usuario: implementar todas las funciones del documento y del diseño, con controles operativos, resultados medibles y buenas prácticas, incluidos principios SOLID.

Fuentes revisadas:

- `Componente_Practico_Smart_Campus_Vision.pdf`: 122 páginas; requisitos en páginas 47–52, historias en 52–66 y arquitectura en 105–119.
- `SmartCampusVision PROTOTIPO.zip`: 22 imágenes PNG. No contiene código fuente ni un archivo Figma editable.

El PDF es una especificación del producto y una referencia académica. Sus menciones de JIRA, AWS y servicios externos no autorizan por sí mismas crear cuentas, publicar información o contratar infraestructura.

Avance actual: hitos 1 a 8 implementados con los alcances documentados. La matriz actualizada de funciones, evidencia y validaciones pendientes está en [estado-y-entrega.md](estado-y-entrega.md). El plan de este documento conserva los criterios de aceptación originales; no implica que se haya aprobado la precisión del modelo ni un despliegue real.

## Matriz funcional

| ID | Comportamiento requerido | Evidencia de aceptación prevista |
| --- | --- | --- |
| RF-01 | Cargar video grabado | MP4 válido procesable; archivo inválido rechazado con error comprensible |
| RF-02 | Detectar personas | Conteos por fotograma y cajas reales; cero detecciones es un resultado válido |
| RF-03 | Detectar y contar puestos | Detecciones vinculadas al video y evaluación manual de puestos; no confundir objetos distintos con puestos adicionales |
| RF-04 | Estimar capacidad y ocupación | Fórmula documentada, origen del dato y tratamiento de capacidad desconocida o cero |
| RF-05 | Registrar aulas y laboratorios | Registro persistente, validaciones y control de permisos |
| RF-06 | Consultar y editar espacios | Cambios persistentes, detalle y listas coherentes |
| RF-07 | Gestionar datos académicos simulados | Cursos, docentes, asignaturas, matrícula entera no negativa y franjas horarias |
| RF-08 | Consultar alternativas | Excluir espacios incompatibles e indicar motivos cuando no haya alternativas |
| RF-09 | Recomendar asignaciones | Capacidad validada, disponibilidad, equipamiento y conflictos evaluados; propuesta sin aplicación automática |
| RF-10 | Detectar conflictos | Casos de solapamiento de aula y docente; horarios contiguos válidos |
| RF-11 | Analizar video en vivo | Probar fuente, ejecutar detecciones, finalizar y liberar cámara; comunicar pérdida de conexión |
| RF-12 | Gestionar reglas y restricciones | Reglas duras y preferencias persistentes; impedir duplicados y contradicciones |
| RF-13 | Validar capacidad estimada | Registrar valor estimado, valor validado, responsable y fecha; usar capacidad validada en recomendaciones |
| RF-14 | Consultar alertas | Filtros y estados nueva/en revisión/resuelta persistentes; vínculo al análisis |
| RF-15 | Consultar propuestas | Mostrar curso, matrícula, espacio, horario y motivos de compatibilidad |
| RF-16 | Aceptar, modificar o rechazar | Confirmación; revalidación al modificar; auditoría; impedir decisiones duplicadas o concurrentes incompatibles |
| RF-17 | Consultar historial | Análisis, alertas y decisiones consultables y filtrables después de reiniciar |
| RF-18 | Generar reportes | PDF real descargable, filtros aplicados y cifras reproducibles desde la base de datos |
| RF-19 | Registro y sesiones | Registro, inicio y cierre reales; impedir acceso a operaciones protegidas sin sesión |
| RF-20 | Recuperar y cambiar contraseña | Enlace temporal de un solo uso, validaciones y cambio efectivo de credenciales |
| RF-21 | Roles y permisos | Administrador, coordinador y usuario registrado; autorización aplicada en el servidor |
| RF-22 | Dashboard | Indicadores y gráficos obtenidos de datos persistidos, con estados vacíos |

## Inventario de pantallas y controles

| Pantalla PNG | Controles y comportamiento que se implementarán |
| --- | --- |
| Login | Usuario/correo, contraseña, iniciar sesión, registrarse y recuperación |
| LoginError | Error real de autenticación; campos accesibles y posibilidad de reintento |
| Registro | Nombre, correo, contraseña, crear cuenta y volver al acceso |
| RecuperarContraseña | Enviar recuperación y volver al acceso |
| CambioContraseña | Nueva contraseña, confirmación, mostrar/ocultar y restablecer |
| Dashboard | Contadores, ocupación y navegación global |
| Analisis | Selección de archivo local o cámara |
| cargar video | Aula, curso, actividad, selección/arrastre del archivo, resumen e iniciar |
| Procesamiento | Progreso real, detecciones, contexto y acceso al resultado al finalizar |
| Resultado análisis | Métricas, sobreocupación, PDF, nuevo análisis y guardado |
| configAnalisisEnVivo | Aula, curso, actividad, cámara, prueba e inicio |
| ProcesamientoEnVivo | Imagen y detecciones actuales, métricas y finalizar |
| ResultadoAnálisisEnVivo | Resultado final, PDF, descarga de grabación cuando exista, guardado y nuevo análisis |
| Aulas | Filtro, nueva aula/laboratorio, editar y ver |
| NuevaAula | Nombre, tipo, capacidad, cámara, estado, guardar y cancelar |
| VerAula | Información, ocupación, actividad reciente, historial, reporte y edición |
| Alertas | Pestañas por estado, acceso al análisis y cambio de estado |
| Horarios | Aula, semana, ocupación por franja y sugerencias calculadas |
| Historial | Filtros por fecha, aula, actividad y fuente; buscar, ver y descargar PDF |
| Reportes | Periodo, actividad, aula, curso, generar, detalle y descarga |
| ReporteDetallado | Resumen, evolución, horas de mayor ocupación y descarga |
| Configuración | Perfil, contraseña, confianza, guardado automático, PDF automático, grabación, alertas, umbral, formato de fecha y guardar |

Todos los menús laterales, enlaces y botones de sesión deben funcionar. Todo control debe tener estado de carga, resultado o error cuando corresponda. Los valores de los PNG no se copiarán como resultados operativos.

## Funciones que requieren ampliar el diseño

Las 22 pantallas no representan por completo los requisitos del PDF. Para cubrirlos se necesitan vistas, pestañas o diálogos adicionales, manteniendo el estilo existente:

1. Datos académicos: cursos, asignaturas, docentes, matrícula y franjas.
2. Reglas y restricciones duras/blandas.
3. Propuestas de asignación, detalle, decisión, modificación y motivo de rechazo.
4. Validación humana de la capacidad estimada.
5. Administración de roles y usuarios.
6. Historial de decisiones y alertas, además del historial de análisis.
7. Edición de perfil y de aula, estados vacíos, fallos de cámara y procesamiento fallido.

## Calidad medible

| ID | Condición del PDF | Verificación prevista |
| --- | --- | --- |
| RNF-01 | Error máximo ±2 personas | Videos reales con conteo manual por fotograma de referencia; registrar errores y casos fuera del límite |
| RNF-02 | Persistencia | Crear/editar datos, reiniciar servicios y comprobar conservación |
| RNF-03 | MP4 como mínimo | Video válido, archivo corrupto, formato no admitido y límites de tamaño |
| RNF-04 | Recomendación en ≤8 s | Medir tiempo con conjunto de datos y hardware documentados |
| RNF-05 | Dashboard en ≤5 s | Medir carga principal en navegador bajo condiciones documentadas |
| RNF-06 | Hash de contraseñas | Verificar almacenamiento seguro y ausencia de contraseñas en respuestas y registros |
| RNF-07 | Permisos | Matriz de pruebas por rol, incluyendo peticiones directas al servidor |
| RNF-08 | Errores de video aislados | Archivo inválido y servicio caído; gestión administrativa sigue operativa |
| RNF-09 | API de visión documentada | Contrato de entrada, resultados, estados, errores y pruebas de integración |
| RNF-10 | Chrome y Edge | Recorridos principales y captura de cámara en ambos navegadores |
| RNF-11 | Sin reconocimiento facial | Revisar modelo de datos y canal de procesamiento; no identificar personas |
| RNF-12 | Desplegable en AWS | Configuración reproducible, almacenamiento persistente, secretos externos y comprobación de despliegue cuando exista infraestructura |

Los objetivos de rendimiento y precisión no están validados actualmente. Las pruebas de código por sí solas no acreditan la precisión visual ni un despliegue real.

## Decisiones de implementación propuestas

- Conservar el backend modular Django/DRF y PostgreSQL previstos en el PDF.
- Mantener la visión en un servicio independiente con una API explícita.
- Interfaz propuesta: React y TypeScript; confirmar restricciones académicas adicionales.
- Separar presentación, validación de solicitudes, servicios de aplicación, reglas de dominio y acceso a datos.
- Aplicar SOLID mediante responsabilidades delimitadas e interfaces en los puntos variables: detector, almacenamiento de archivos, correo y generación de reportes.
- Ejecutar análisis fuera del ciclo de la petición web; definir estados de trabajo y recuperación ante fallo.
- Proteger archivos y resultados mediante autorización; evitar que conocer una URL permita acceder a videos ajenos.
- Autorizar registros públicos con un rol de privilegios mínimos; la interfaz no puede conceder permisos administrativos.
- Usar datos académicos de demostración identificados como simulados, conforme al PDF.
- Definir la agregación de conteos (por ejemplo, máximo y promedio) antes de presentar una cifra final. No sumar detecciones de distintos fotogramas como si fueran personas únicas.
- Mantener separadas capacidad estimada, capacidad validada y ocupación observada.
- No presentar una cámara como disponible sin probarla, ni un resultado fallido como un conteo de cero.
- Cuando no haya capacidad válida, presentar ocupación como no calculable; no dividir por cero.

## Secuencia de construcción

1. Estructura del proyecto, configuración, PostgreSQL, cuentas, roles y pruebas base.
2. Prueba técnica de visión con videos de referencia y definición verificable de puesto de trabajo.
3. Gestión de aulas y datos académicos, validación de capacidad.
4. Análisis grabado y en vivo, estados de procesamiento, almacenamiento y alertas.
5. Reglas, conflictos, recomendaciones y decisiones auditables.
6. Dashboard, historial, reportes y configuración conectados a datos reales.
7. Revisión de las 22 pantallas, pruebas integrales de controles, rendimiento y preparación de despliegue.

Cada bloque debe incluir sus pruebas antes de considerarse terminado.

## Información externa pendiente

- Se recibieron cuatro videos de la propuesta y se verificó su apertura y la lectura de tres fotogramas por archivo. Faltan etiquetas/conteos manuales y material representativo para validar RNF-01 y la detección de puestos. Véase `videos-y-modelo.md`.
- Disponibilidad de cámara USB/integrada y, si se probará RTSP, una fuente accesible.
- Requisitos tecnológicos confirmados: Django, DRF, AWS, uno o más microservicios y librería de IA. El curso de certificación de Amazon corresponde al estudiante.
- Proveedor de correo para validar recuperación por correo en un entorno externo; durante desarrollo puede usarse un buzón local de pruebas.
- Infraestructura AWS solo cuando corresponda realizar el despliegue; no es necesaria para comenzar el desarrollo local.

No se requieren credenciales sensibles en el chat. Los secretos se configurarán localmente mediante variables de entorno.

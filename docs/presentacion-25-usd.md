# Presentación en AWS con presupuesto total de US$25

Revisión: 9 de noviembre de 2026. El usuario creó `SmartCampus-demo` en Lightsail Ohio (`us-east-2a`), Ubuntu 24.04 x86-64, 8 GB RAM, 2 vCPU y 160 GB SSD, plan visible de US$44/mes. El recurso ya existe y puede generar cargos. Docker y Compose fueron verificados con `hello-world`. El código y los pesos se transfirieron por SSH. Las 73 pruebas Django pasaron sobre PostgreSQL 17 en una base temporal del servidor (68,583 segundos), usando `DJANGO_DEBUG=true` solo en el contenedor de pruebas y las dependencias de `requirements-dev.txt`. La imagen de visión se ajustó para usar PyTorch CPU y evitar CUDA. La web pública aún no está acreditada.

## Condiciones confirmadas

Presentación el 10 de noviembre de 2026; mantener la web como máximo 48 horas. Presupuesto preferido US$20–30; el usuario dispone de US$50–75 como máximo. La cuenta AWS ya está disponible; no tiene dominio. Se eligió un servidor de 8 GB durante la ventana breve, pendiente de medición: 48 horas son aproximadamente US$2,82 de instancia usando US$44/750 horas, antes de impuestos y extras.

Crear la cuenta hoy: AWS indica que la activación puede tardar hasta 24 horas ([registro](https://docs.aws.amazon.com/accounts/latest/reference/getting-started.html)). Elegir soporte básico sin suscripción pagada y verificar qué plan de cuenta permite Lightsail antes de confirmar. No entregar contraseñas, códigos MFA ni claves de acceso por chat.

Sin dominio comprado, se puede probar un nombre `campus-IP-CON-GUIONES.sslip.io` con la IP pública del servidor, por ejemplo `campus-203-0-113-10.sslip.io` (la IP del ejemplo es documental y debe sustituirse). Verificar que el nombre resuelva a la IP real antes de iniciar Caddy. Configurar ese nombre sin protocolo en `SITE_ADDRESS`, añadirlo a `DJANGO_ALLOWED_HOSTS` conservando `localhost,127.0.0.1,backend`, y usar `https://NOMBRE` en `FRONTEND_URL` y `CSRF_TRUSTED_ORIGINS`. Abrir 80/443 y comprobar el certificado y la cámara desde el navegador. Es un servicio DNS de terceros; la emisión puede fallar por límites o disponibilidad y debe verificarse. Fuentes: [nip.io/sslip.io](https://nip.io/), [Caddy HTTPS](https://caddyserver.com/docs/quick-starts/https).

## Arquitectura propuesta

HTTPS verificado el 9 de noviembre de 2026 después de habilitar TCP 443: `https://campus-18-227-0-9.sslip.io/login` devuelve HTTP/2 200 y `/health/` devuelve `{"status": "ok"}` con verificación TLS habilitada. Pendientes: crear administrador, cargar o migrar catálogos y probar flujos desde el navegador público. Estas comprobaciones sustituyen el timeout de acceso indicado en el avance anterior.

Avance verificado en AWS: PostgreSQL, visión y backend reportan salud correcta; trabajador y gateway arrancaron. Migraciones y recopilación de estáticos completadas; `manage.py check --deploy` sin incidencias. Inferencia real de YOLO sobre una imagen sintética vacía ejecutada con PyTorch `2.14.1+cpu`; esto verifica ejecución, no precisión. Se corrigió en `services/vision/app/settings.py` el acceso a ancestros de `/app` que impedía iniciar en Docker. La prueba HTTPS pública agotó 12 segundos; queda pendiente revisar el firewall HTTP/HTTPS en Lightsail, emitir certificado y probar los flujos públicos. No se han importado los datos locales ni creado aún la cuenta administradora. El correo usa archivos en el contenedor; SMTP externo sigue pendiente.

Usar la pila existente `compose.deploy.yaml` en una sola instancia Lightsail Linux x86-64: React/Caddy con HTTPS, Django, trabajador, YOLO y PostgreSQL con volumen persistente. PostgreSQL estará en la nube dentro del servidor AWS; no será una base administrada independiente. No publicar el puerto de PostgreSQL.

Para una demostración breve, probar inicialmente 4 GB de RAM y 2 vCPU. Es un punto de partida, no una garantía para YOLO: medir memoria, análisis de un video corto y cámara antes de presentar. Si requiere más memoria, cotizar una instancia mayor durante menos días. Evitar análisis simultáneos durante la prueba inicial.

## Costos y duración

AWS publica US$24/mes para el paquete Linux de 4 GB con IPv4 y US$44/mes para 8 GB. Se factura por horas hasta el máximo mensual. Confirmar la tarifa horaria y región en la consola antes de crear el servidor. Como referencia aproximada usando 750 horas mensuales:

| Paquete | 72 horas | 7 días | Mes completo |
| --- | ---: | ---: | ---: |
| 4 GB | US$2,30 | US$5,38 | US$24 |
| 8 GB | US$4,22 | US$9,86 | US$44 |

Las cifras excluyen impuestos, dominio, snapshots, almacenamiento adicional y exceso de transferencia; no son una cotización final. No depender de promociones o créditos sin verificar la elegibilidad de la cuenta. Reservar margen y buscar un subtotal de infraestructura inferior a US$15. Un mes completo del plan de US$24 no deja margen suficiente para asegurar un total menor de US$25.

Una base administrada Lightsail comienza en US$15/mes adicionales. Para esta presentación se propone PostgreSQL en el mismo servidor. Si la rúbrica exige RDS o una base administrada separada, recalcular la arquitectura y el tiempo antes de crear recursos.

Fuentes oficiales: [paquetes Lightsail](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html), [facturación y prorrateo](https://aws.amazon.com/lightsail/faq/), [bases administradas](https://docs.aws.amazon.com/en_en/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html).

## Orden de ejecución

1. Ejecutar las pruebas locales y las de PostgreSQL en CI. El workflow `checks.yml` ahora contempla ambos motores; añadirlo no implica que ya se haya ejecutado en GitHub.
2. Completar evaluación de conteos con anotaciones humanas y medir rendimiento. El conteo actual de monitores no acredita puestos utilizables.
3. Confirmar fecha, días activos, región AWS, acceso a la cuenta y un dominio/subdominio para HTTPS. La cámara del navegador requiere HTTPS fuera de localhost. Usar un subdominio disponible evita comprar un dominio solo para presentar.
4. Crear presupuesto con avisos antes de US$10, US$15 y US$20. Los avisos pueden retrasarse y no imponen un límite duro de gasto: [documentación de AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html).
5. Construir y verificar la pila siguiendo [despliegue AWS](despliegue-aws.md). Probar roles, videos, cámara, PDFs y correo desde la URL pública. Registrar consumo y tiempos.
6. Para conservar datos locales, ensayar exportación/importación a PostgreSQL en una base aparte y verificar relaciones, usuarios y archivos. Cambiar variables de conexión no migra los datos. No sobrescribir la base local.
7. Tras presentar, descargar y verificar respaldo de base y archivos. Solo entonces eliminar los recursos temporales desde la cuenta del titular y revisar la facturación y recursos restantes. Detener Lightsail sigue generando cargos; snapshots e IP sin asociar pueden generar cargos aparte. El borrado definitivo requiere decidir qué datos conservar.

## Evidencia pendiente

Este equipo no dispone de Docker, PostgreSQL ni AWS CLI en PATH en la revisión inicial. Las pruebas locales SQLite y la compilación no verifican Linux, PostgreSQL, HTTPS público ni rendimiento en Lightsail. No registrar el proyecto como desplegado hasta comprobar la URL y los flujos reales.

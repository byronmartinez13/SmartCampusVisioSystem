# Preparación de despliegue en AWS

Estado al 10 de noviembre de 2026: **pila Docker construida y desplegada en AWS Lightsail**, Ubuntu 24.04 x86-64, 8 GB RAM y 2 vCPU. PostgreSQL 17, backend y visión reportan salud correcta; HTTPS y acceso público fueron verificados. El usuario confirmó login y uso de iVCam. El servidor es temporal y consume recursos/créditos de AWS; no confundir el plan gratuito de la cuenta con una instancia sin consumo. Ver [plan de presentación](presentacion-25-usd.md). Este equipo local no dispone de Docker: la construcción Linux se realizó por SSH en AWS.

## Arquitectura incluida

`compose.deploy.yaml` define PostgreSQL, Django/Gunicorn, un trabajador de videos, FastAPI/YOLO y un gateway Caddy con frontend compilado y HTTPS. Solo el gateway publica puertos. Base de datos, medios privados, cola de visión y certificados usan volúmenes persistentes. Django usa caché compartida en PostgreSQL para límites de solicitudes.

Es una instalación de un solo servidor para la presentación. No ofrece alta disponibilidad ni escalado horizontal del detector/cola. No ejecutar más de una instancia del trabajador ni varios workers Uvicorn con esta cola.

## Antes de ejecutar

1. Disponer de un servidor Linux x86-64, Docker Engine y Compose v2. Construir y medir primero con el hardware que se usará; no se ha establecido un tamaño de instancia que garantice los objetivos del proyecto.
2. Copiar el repositorio sin `.env`, bases SQLite, videos personales ni correos locales. Transferir los pesos `yolo11n.pt` a `services/vision/models/` o adaptar la ruta si el grupo usa otro modelo. El servicio no descarga pesos automáticamente.
3. Copiar `deploy/env.deploy.example` a `.env.deploy` en la raíz y sustituir todos los valores de ejemplo. Mantener permisos de archivo restringidos. Usar secretos independientes para Django, PostgreSQL y visión. No enviar esos valores por chat ni subirlos a Git.
4. Configurar un dominio con DNS hacia el servidor y completar `SITE_ADDRESS`, `FRONTEND_URL`, `DJANGO_ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`. La cámara del navegador requiere HTTPS fuera de localhost. Caddy solicita el certificado cuando el dominio y el acceso a sus puertos funcionan.
5. Configurar SMTP real y comprobar recuperación de contraseña. La entrega de correo externo no ha sido probada.

En EC2, habilitar HTTP/HTTPS para la aplicación y restringir SSH a las IP de administración según [las reglas de grupos de seguridad de AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html). No abrir 5432, 8000 ni 8002 públicamente.

## Arranque en el servidor

Desde la raíz:

```bash
docker compose -f compose.deploy.yaml --env-file .env.deploy config --quiet
docker compose -f compose.deploy.yaml --env-file .env.deploy build
docker compose -f compose.deploy.yaml --env-file .env.deploy up -d
docker compose -f compose.deploy.yaml --env-file .env.deploy ps
docker compose -f compose.deploy.yaml --env-file .env.deploy exec backend python manage.py check --deploy
docker compose -f compose.deploy.yaml --env-file .env.deploy exec backend python manage.py createsuperuser
```

No existe contraseña predeterminada. El backend ejecuta migraciones, crea la tabla de caché y recopila estáticos antes de iniciar Gunicorn. La salud comprueba acceso a la base; no certifica la precisión ni rapidez de YOLO. El servicio de visión verifica también la presencia del archivo de pesos.

Abrir `https://DOMINIO/health/`, registrar una cuenta de prueba, verificar roles, subir un video, guardar su resultado, descargar PDF y probar cámara. Revisar los logs mediante `docker compose -f compose.deploy.yaml logs --tail 100 backend worker vision gateway`.

## Datos y respaldos

SQLite de desarrollo no se copia automáticamente a PostgreSQL. Para una demostración nueva, crear catálogos verificados y cuentas nuevas. Si se deben migrar datos existentes, ensayar exportación/importación y validar identificadores y relaciones en una base aparte antes de cambiar el entorno del grupo.

Respaldar PostgreSQL con `pg_dump` y conservar copias de los volúmenes `private_media` y `vision_data`, junto con los pesos del modelo y la configuración fuera del repositorio. Los backups de usuarios contienen hashes de contraseña: requieren acceso restringido. Probar la restauración en un entorno separado y registrar fecha y resultado.

EBS permite respaldar volúmenes mediante snapshots; coordinar la consistencia de datos y archivos, y establecer retención según el grupo. [Documentación oficial de snapshots](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-creating-snapshot.html). Configurar también presupuesto y alertas de facturación en la cuenta que use el grupo.

No usar `docker compose down -v` para detener la aplicación: borra volúmenes. `docker compose -f compose.deploy.yaml stop` conserva los datos.

## Condiciones pendientes para producción

- Construcción Linux, migraciones PostgreSQL, `check --deploy` y salud HTTPS verificados. Ampliar las pruebas de carga y de decisiones concurrentes en el servidor real.
- Ensayo completo con cámara física, red y equipo de presentación; SMTP externo y restauración de backup pendientes.
- Medición de memoria, latencia y capacidad bajo carga. Dos detectores CPU (video/cámara) pueden competir por recursos.
- Política institucional de conservación y eliminación de archivos. La aplicación no borra videos automáticamente.
- Si se necesita continuidad de servicio, diseñar aparte RDS/almacenamiento externo, observabilidad y una cola apta para varios trabajadores. La pila incluida no acredita esas propiedades.
